"""Structure graph module.

The goal of this module is the static analysis of the JSON file. We convert the initial
JSON to a so-called "structure graph", which is a Python representation of the JSON
containing the nodes (Metadata, FileObject, etc) and the hierarchy between them. In the
process of parsing all the nodes, we also check that no information is missing and raise
issues (errors or warnings) when necessary. See the docstring of
`from_nodes_to_structure_graph` for more information.

The important functions of this module are:
- from_file_to_json             file -> JSON
- from_json_to_rdf              JSON -> RDF
- from_rdf_to_nodes             RDF -> nodes
- from_nodes_to_structure_graph nodes -> structure graph

TODO(https://github.com/mlcommons/croissant/issues/114):
A lot of methods in this file share common data structures (issues, graph, folder, etc),
so they should be grouped under a common `StructureGraph` class.
"""

from __future__ import annotations

import dataclasses
import json

from etils import epath
import networkx as nx
import rdflib

from ml_croissant._src.core import constants
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.core.json_ld import from_jsonld_to_json
from ml_croissant._src.core.types import Json
from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.nodes.field import Field
from ml_croissant._src.structure_graph.nodes.file_object import FileObject
from ml_croissant._src.structure_graph.nodes.file_set import FileSet
from ml_croissant._src.structure_graph.nodes.metadata import Metadata


def from_file_to_jsonld(filepath: epath.PathLike) -> tuple[epath.Path, list[Json]]:
    """Loads the file as a JSON-LD.

    Args:
        filepath: The path to the file as a str or a path. The path can be absolute or
            relative.

    Returns:
        A tuple with the absolute path to the file and the JSON-LD.
    """
    filepath = epath.Path(filepath).expanduser().resolve()
    if not filepath.exists():
        raise ValueError(f"File {filepath} does not exist.")
    with filepath.open() as f:
        data = json.load(f)
    graph = rdflib.Graph()
    graph.parse(
        data=data,
        format="json-ld",
    )
    # `graph.serialize` outputs a stringified list of JSON-LD nodes.
    nodes = graph.serialize(format="json-ld")
    nodes = json.loads(nodes)
    return filepath, nodes


def from_nodes_to_graph(metadata: Metadata) -> nx.MultiDiGraph:
    """Converts the metadata to a structure graph linking nodes to their sources."""
    graph = nx.MultiDiGraph()
    # Bind graph to nodes:
    for node in metadata.nodes():
        node.graph = graph
        graph.add_node(node)
    uid_to_node = _check_no_duplicate(metadata)
    for node in metadata.distribution:
        if node.contained_in:
            for uid in node.contained_in:
                _add_edge(graph, uid_to_node, uid, node)
    for record_set in metadata.record_sets:
        for field in record_set.fields:
            if record_set.data:
                _add_edge(graph, uid_to_node, record_set.uid, field)
            for origin in [field.source, field.references]:
                if origin:
                    _add_edge(graph, uid_to_node, origin.uid, field)
            for sub_field in field.sub_fields:
                for origin in [sub_field.source, sub_field.references]:
                    if origin:
                        _add_edge(graph, uid_to_node, origin.uid, sub_field)
    # `Metadata` are used as the entry node.
    _add_node_as_entry_node(graph, metadata)
    return graph


def from_json_to_rdf(data: Json) -> rdflib.Graph:
    """Converts the JSON to an RDF graph with expanded JSON-LD attributes using RDFLib.

    We use RDFLib instead of reinventing a JSON-LD parser. This may be more cumbersome
    short-term, but will prove handy long-term, when we integrate more advanced feature
    of RDF/JSON-LD, or other parsers (e.g., YAML-LD).

    We prefer the RDF graph representation over the JSON-LD representation because the
    former is easier to traverse the graph than the JSON.

    Args:
        data: The JSON dict.

    Returns:
        A tuple with the RDF namespace manager (see:
            https://rdflib.readthedocs.io/en/stable/namespaces_and_bindings.html) and
            the RDF graph.
    """
    graph = rdflib.Graph()
    graph.parse(
        data=data,
        format="json-ld",
    )
    return graph


@dataclasses.dataclass
class Structure:
    """Represents the structure of the Croissant file.

    Args:
        issues: The issues to populate in case of problem.
        graph: The graph linking each node (Metadata, FileSet, FileObject, RecordSet and
            Fields) to their sources. For example, a Field may be contained in a
            RecordSet, but its true original source in the `graph` will be the
            FileObject it originates from.
        metadata: The Python representation of the Croissant JSON-LD file (e.g., the
            metadata node has a distribution and record sets, etc). See the Croissant
            specs on GitHub for more info on how the Croissant JSON-LD is structured.
        filepath: The path to the Croissant file if it exists.
    """

    issues: Issues
    metadata: Metadata
    filepath: epath.Path | None
    graph: nx.MultiDiGraph = dataclasses.field(init=False)

    def __post_init__(self):
        self.graph = from_nodes_to_graph(self.metadata)

    @classmethod
    def from_json(
        cls, issues: Issues, json_: Json, filepath: epath.Path | None = None
    ) -> Structure:
        """Creates the Structure from a Croissant JSON-LD."""
        folder = filepath.parent if filepath else None
        metadata = Metadata.from_jsonld(issues, folder, json_)
        return cls(issues=issues, metadata=metadata, filepath=filepath)

    @classmethod
    def from_file(cls, issues: Issues, file: epath.PathLike) -> Structure:
        """Creates the Structure from a Croissant file."""
        filepath, jsonld = from_file_to_jsonld(file)
        json_ = from_jsonld_to_json(jsonld)
        return cls.from_json(issues, json_, filepath=filepath)

    def check_graph(self):
        """Checks the integrity of the structure graph.

        The rules are the following:
        - The graph is directed.
        - All fields have a data type: either directly specified, or on a parent.

        Args:
            issues: The issues to populate in case of problem.
            graph: The structure graph to be checked.
        """
        # Check that the graph is directed.
        if not self.graph.is_directed():
            self.issues.add_error("The structure graph is not directed.")
        fields = [node for node in self.graph.nodes if isinstance(node, Field)]
        # Check all fields have a data type: either on the field, on a parent.
        for field in fields:
            field.actual_data_type


def get_entry_nodes(graph: nx.MultiDiGraph) -> list[Node]:
    """Retrieves the entry nodes (without predecessors) in a graph."""
    entry_nodes: list[Node] = []
    for node, indegree in graph.in_degree(graph.nodes()):
        if indegree == 0:
            entry_nodes.append(node)
    # Fields should usually not be entry nodes, except if they have subFields. So we
    # check for this:
    for node in entry_nodes:
        if isinstance(node, Field) and not node.sub_fields and not node.data:
            if not node.source:
                node.add_error(
                    f'Node "{node.uid}" is a field and has no source. Please, use'
                    f" {constants.ML_COMMONS_SOURCE} to specify the source."
                )
            else:
                uid = node.source.uid
                node.add_error(
                    f"Malformed source data: {uid}. It does not refer to any existing"
                    f" node. Have you used {constants.ML_COMMONS_FIELD} or"
                    f" {constants.SCHEMA_ORG_DISTRIBUTION} to indicate the source field"
                    " or the source distribution? If you specified a field, it should"
                    " contain all the names from the RecordSet separated by `/`, e.g.:"
                    ' "record_set_name/field_name"'
                )
    return entry_nodes


def _check_no_duplicate(metadata: Metadata) -> dict[str, Node]:
    """Checks that no node has duplicated UID and returns the mapping `uid`->`Node`."""
    uid_to_node: dict[str, Node] = {}
    for node in metadata.nodes():
        if node.uid in uid_to_node:
            node.add_error(
                f"Duplicate nodes with the same identifier: {uid_to_node[node.uid].uid}"
            )
        uid_to_node[node.uid] = node
    return uid_to_node


def _add_node_as_entry_node(graph: nx.MultiDiGraph, node: Node):
    """Add `node` as the entry node of the graph by updating `graph` in place."""
    graph.add_node(node, parent=None)
    entry_nodes = get_entry_nodes(graph)
    for entry_node in entry_nodes:
        if isinstance(node, (FileObject, FileSet)):
            graph.add_edge(entry_node, node)


def _add_edge(
    graph: nx.MultiDiGraph,
    uid_to_node: dict[str, Node],
    uid: str,
    node: Node,
):
    """Adds an edge in the structure graph."""
    if uid not in uid_to_node:
        node.add_error(
            f'There is a reference to node named "{uid}" in node "{node.uid}", but this'
            " node doesn't exist."
        )
        return
    graph.add_edge(uid_to_node[uid], node)
