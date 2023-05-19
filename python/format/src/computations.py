"""computations module."""

from collections.abc import Callable, Mapping
import dataclasses
import fnmatch
import hashlib
import os
import re
import tarfile
from typing import Any

from absl import logging
from etils import epath
from format.src.errors import Issues
from format.src.nodes import (
    concatenate_uid,
    Field,
    FileObject,
    FileSet,
    Metadata,
    Node,
    RecordSet,
    Source,
)
import networkx as nx
import pandas as pd
import requests
import tqdm

_CROISSANT_CACHE = epath.Path("/tmp/croissant")
_DOWNLOAD_PATH = _CROISSANT_CACHE / "download"
_EXTRACT_PATH = _CROISSANT_CACHE / "extract"
_DOWNLOAD_CHUNK_SIZE = 1024


def _get_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def _tmp_column_name(original_name: str) -> str:
    return f"{original_name}_{_get_hash(original_name)}"


def _get_download_filepath(url: str) -> epath.Path:
    hashed_url = _get_hash(url)
    _DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
    return _DOWNLOAD_PATH / f"croissant-{hashed_url}"


def get_entry_nodes(graph: nx.MultiDiGraph) -> list[Node]:
    """Retrieves the entry nodes (without predecessors) in a graph."""
    entry_nodes = []
    for node, indegree in graph.in_degree(graph.nodes()):
        if indegree == 0:
            entry_nodes.append(node)
    return entry_nodes


def _check_no_duplicate(issues: Issues, nodes: list[Node]) -> Mapping[str, Node]:
    """Checks that no node has duplicated UID and returns the mapping `uid`->`Node`."""
    uid_to_node: Mapping[str, Node] = {}
    for node in nodes:
        if node.uid in uid_to_node:
            issues.add_error(f"Duplicate node with the same identifier: {node.uid}")
        uid_to_node[node.uid] = node
    return uid_to_node


def add_node_as_entry_node(graph: nx.MultiDiGraph, node: Node):
    """Add `node` as the entry node of the graph by updating `graph` in place."""
    graph.add_node(node, parent=None)
    entry_nodes = get_entry_nodes(graph)
    for entry_node in entry_nodes:
        if isinstance(node, (FileObject, FileSet)):
            graph.add_edge(entry_node, node)


def add_edge(
    issues: Issues,
    graph: nx.MultiDiGraph,
    uid_to_node: Mapping[str, Node],
    uid: str,
    node: Node,
):
    if uid not in uid_to_node:
        issues.add_error(
            f'There is a reference to node named "{uid}", but this node doesn\'t exist.'
        )
        return
    graph.add_edge(uid_to_node[uid], node)


def build_structure_graph(
    issues: Issues, nodes: list[Node]
) -> tuple[Node, nx.MultiDiGraph]:
    """Builds the structure graph from the nodes.

    The structure graph represents the relationship between the nodes:

    - For ml:Fields without ml:subField, the predecessors in the structure graph are the
    sources.
    - For sc:FileSet or sc:FileObject with a `containedIn`, the predecessors in the
    structure graph are those `containedId`.
    - For other objects, the predecessors are their parents (i.e., predecessors in the
    JSON-LD). For example: for ml:Field with subField, the predecessors are the
    ml:RecordSet in which they are contained.
    """
    graph = nx.MultiDiGraph()
    uid_to_node = _check_no_duplicate(issues, nodes)
    for node in nodes:
        if isinstance(node, Metadata):
            continue
        parent = uid_to_node[node.parent_uid]
        graph.add_node(node, parent=parent)
        # Distribution
        if isinstance(node, (FileObject, FileSet)) and node.contained_in:
            for uid in node.contained_in:
                add_edge(issues, graph, uid_to_node, uid, node)
        # Fields
        elif isinstance(node, Field):
            references = []
            if node.source is not None:
                references.append(node.source.reference)
            if node.references is not None:
                references.append(node.references.reference)
            for reference in references:
                # The source can be either another field...
                if (uid := concatenate_uid(reference)) in uid_to_node:
                    add_edge(issues, graph, uid_to_node, uid, node)
                # ...or the source can be a metadata.
                elif (uid := reference[0]) in uid_to_node:
                    add_edge(issues, graph, uid_to_node, uid, node)
                else:
                    issues.add_error(
                        "Source refers to an unknown node"
                        f' "{concatenate_uid(reference)}".'
                    )
        # Other nodes
        elif node.parent_uid is not None:
            add_edge(issues, graph, uid_to_node, node.parent_uid, node)
    # `Metadata` are used as the entry node.
    metadata = next((node for node in nodes if isinstance(node, Metadata)), None)
    if metadata is None:
        issues.add_error("No metadata is defined in the dataset.")
        return None, graph
    add_node_as_entry_node(graph, metadata)
    if not graph.is_directed():
        issues.add_error("Structure graph is not directed.")
    return metadata, graph


@dataclasses.dataclass(frozen=True, repr=False)
class Operation:
    """Generic base class to define an operation.

    `@dataclass(frozen=True)` allows having a hashable operation for NetworkX to use
    operations as nodes of  graphs.

    `@dataclass(repr=False)` allows having a readable stringified `str(operation)`.

    Args:
        node: The node attached to the operation for the context.
        output: The result of the operation when it is executed (as returned by
            __call__).
    """

    node: Node

    def __call__(self):
        raise NotImplementedError

    def __repr__(self):
        return f"{type(self).__name__}({self.node.uid})"


class FileOperation(Operation):
    def __call__(self):
        raise NotImplementedError


class LineOperation(Operation):
    def __call__(self):
        raise NotImplementedError


@dataclasses.dataclass(frozen=True, repr=False)
class InitOperation(Operation):
    """Sets up other operations."""

    def __call__(self):
        logging.info("Setting up generation for dataset: %s", self.node_uid)


@dataclasses.dataclass(frozen=True, repr=False)
class Download(FileOperation):
    """Downloads from a URL to the disk."""

    url: str

    def __call__(self):
        filepath = _get_download_filepath(self.url)
        if not filepath.exists():
            response = requests.get(self.url, stream=True, timeout=10)
            total = int(response.headers.get("Content-Length", 0))
            with filepath.open("wb") as file, tqdm.tqdm(
                desc=f"Downloading {self.url}...",
                total=total,
                unit="iB",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(chunk_size=_DOWNLOAD_CHUNK_SIZE):
                    size = file.write(data)
                    bar.update(size)
        logging.info("File %s is downloaded to %s.", self.url, os.fspath(filepath))


@dataclasses.dataclass(frozen=True, repr=False)
class Untar(FileOperation):
    """Un-tars "application/x-tar" and yields filtered lines."""

    node: FileObject
    target_node: FileObject | FileSet

    def __call__(self):
        includes = fnmatch.translate(self.target_node.includes)
        url = self.node.content_url
        archive_file = _get_download_filepath(url)
        hashed_url = _get_hash(url)
        extract_dir = _EXTRACT_PATH / hashed_url
        if not extract_dir.exists():
            with tarfile.open(archive_file) as tar:
                tar.extractall(extract_dir)
        logging.info(
            "Found directory where data is extracted: %s.", os.fspath(extract_dir)
        )
        included_files = []
        for basepath, _, files in os.walk(extract_dir):
            for file in files:
                if re.match(includes, os.fspath(file)):
                    included_files.append(epath.Path(basepath) / file)
        return pd.DataFrame(
            {
                "filepath": included_files,
                "filename": [file.name for file in included_files],
            }
        )


@dataclasses.dataclass(frozen=True, repr=False)
class ReadCsv(FileOperation):
    """Reads from a CSV file and yield lines."""

    url: str

    def __call__(self):
        filepath = _get_download_filepath(self.url)
        with filepath.open("rb") as csvfile:
            return pd.read_csv(csvfile)


def apply_transform_fn(value: str, source: Source | None = None) -> Callable[..., Any]:
    if source is None:
        return value
    if source.apply_transform_regex is not None:
        source_regex = re.compile(source.apply_transform_regex)
        match = source_regex.match(value)
        for group in match.groups():
            if group is not None:
                return group
    return value


@dataclasses.dataclass(frozen=True, repr=False)
class Join(LineOperation):
    """Joins pd.DataFrames."""

    def __call__(
        self, *args: pd.Series, left: Source | None = None, right: Source | None = None
    ) -> pd.Series:
        if len(args) == 1:
            return args[0]
        elif len(args) == 2:
            df_left, df_right = args
            assert (
                len(left.reference) == 2
            ), "JOIN operation does not define a column name."
            left_key = left.reference[1]
            right_key = right.reference[1]
            new_left_key = _tmp_column_name(left.reference[1])
            assert left_key in df_left.columns, (
                f'Column "{left_key}" does not exist in node "{left.reference[0]}".'
                f" Existing columns: {df_left.columns}"
            )
            assert right_key in df_right.columns, (
                f'Column "{right_key}" does not exist in node "{right.reference[0]}".'
                f" Existing columns: {df_right.columns}"
            )
            df_left[new_left_key] = df_left[left_key].transform(
                apply_transform_fn, source=left
            )
            return df_left.set_index(new_left_key).join(df_right.set_index(right_key))
        else:
            raise NotImplementedError(
                f"Unsupported: Trying to joing {len(args)} pd.DataFrames."
            )


@dataclasses.dataclass(frozen=True, repr=False)
class ReadField(LineOperation):
    """Reads a field from a Pandas DataFrame and applies transformations."""

    node: Field

    def __call__(self, original: pd.Series) -> Mapping[str, Any]:
        assert isinstance(self.node, Field)
        field = self.node.source.reference[-1]
        assert field in original, (
            f'Field "{field}" does not exist in source "{self.node.parent_uid}".'
            f" Existing fields: {original.keys()}"
        )
        return {self.node.name: original[field]}


@dataclasses.dataclass(frozen=True, repr=False)
class GroupRecordSet(LineOperation):
    """Groups fields as a record set."""

    def __call__(self, *fields: pd.Series):
        concatenated_series = {k: v for field in fields for k, v in field.items()}
        return {self.node.name: concatenated_series}


@dataclasses.dataclass(frozen=True)
class ComputationGraph:
    """Graph of dependent operations to execute to generate the dataset."""

    issues: Issues
    graph: nx.MultiDiGraph

    @classmethod
    def from_nodes(
        cls, issues: Issues, metadata: Node, graph: nx.MultiDiGraph
    ) -> "ComputationGraph":
        """Builds the ComputationGraph from the nodes.

        This is done by:

        1. Building the structure graph.
        2. Building the computation graph by exploring the structure graph layers by
        layers in a breadth-first search.
        """
        last_operation_for_node: Mapping[Node, Operation] = {}
        operations = nx.MultiDiGraph()
        for node in nx.topological_sort(graph):
            predecessors = graph.predecessors(node)
            for predecessor in predecessors:
                if predecessor in last_operation_for_node:
                    last_operation_for_node[node] = last_operation_for_node[
                        predecessor
                    ]
            if isinstance(node, Field):
                if node.source and not node.has_sub_fields:
                    parent_node = graph.nodes[node].get("parent")
                    if node.references is not None:
                        operation = Join(node=parent_node)
                        # `Join()` takes left=Source and right=Source as kwargs.
                        kwargs = {
                            "left": node.source,
                            "right": node.references,
                        }
                        operations.add_node(operation, kwargs=kwargs)
                        for predecessor in graph.predecessors(node):
                            operations.add_edge(
                                last_operation_for_node[predecessor], operation
                            )
                    last_operation_for_node[node] = operation
                    if len(node.source.reference) != 2:
                        issues.add_error(f'Wrong source in node "{node.uid}"')
                        continue
                    operation = ReadField(node=node)
                    operations.add_edge(last_operation_for_node[node], operation)
                    last_operation_for_node[node] = operation
                    if isinstance(parent_node, Field) and isinstance(node, Field):
                        new_operation = Operation(node=parent_node)
                        operations.add_edge(operation, new_operation)
                        operation = new_operation
                        last_operation_for_node[parent_node] = new_operation
                        parent_node = graph.nodes[parent_node].get("parent")
                    if isinstance(parent_node, RecordSet):
                        new_operation = GroupRecordSet(node=parent_node)
                        operations.add_edge(operation, new_operation)
                        operation = new_operation
                        last_operation_for_node[parent_node] = new_operation
            elif isinstance(node, FileObject):
                operation = Download(node=node, url=node.content_url)
                operations.add_node(operation)
                last_operation_for_node[node] = operation
                for successor in graph.successors(node):
                    if (
                        node.encoding_format == "application/x-tar"
                        and isinstance(successor, (FileObject, FileSet))
                        and successor.encoding_format != "application/x-tar"
                    ):
                        operation = Untar(node=node, target_node=successor)
                        operations.add_edge(
                            last_operation_for_node[node], operation
                        )
                        last_operation_for_node[node] = operation
                if node.encoding_format == "text/csv":
                    operation = ReadCsv(
                        node=node,
                        url=node.content_url,
                    )
                    operations.add_edge(last_operation_for_node[node], operation)
                    last_operation_for_node[node] = operation

        # Attach all entry nodes to a single `start` node
        entry_operations = get_entry_nodes(operations)
        init_operation = InitOperation(node=metadata)
        for entry_operation in entry_operations:
            operations.add_edge(init_operation, entry_operation)
        return ComputationGraph(issues=issues, graph=operations)

    def check_graph(self):
        """Checks the computation graph for issues."""
        if not self.graph.is_directed():
            self.issues.add_error("Computation graph is not directed.")
        selfloops = [operation.uid for operation, _ in nx.selfloop_edges(self.graph)]
        if selfloops:
            self.issues.add_error(
                f"The following operations refered to themselves: {selfloops}"
            )
