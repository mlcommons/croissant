"""graph module."""

from collections.abc import Mapping
import dataclasses

from etils import epath
from ml_croissant._src.core import constants
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.nodes import (
    Field,
    FileObject,
    FileSet,
    Metadata,
    RecordSet,
)
from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.operation_graph.operations import (
    Data,
    Download,
    GroupRecordSet,
    InitOperation,
    Join,
    Merge,
    Untar,
    ReadCsv,
    ReadField,
)
from ml_croissant._src.structure_graph.base_node import Node
import networkx as nx
from rdflib import namespace


def concatenate_uid(source: tuple[str]) -> str:
    return "/".join(source)


def _find_record_set(graph: nx.MultiDiGraph, node: Node) -> RecordSet:
    """Finds the record set to which a field is attached.

    The record set will be typically either the parent or the parent's parent.
    """
    parent_node = graph.nodes[node].get("parent")
    if isinstance(parent_node, RecordSet):
        return parent_node
    elif parent_node is None:
        raise ValueError(f"Node {node} is not in a RecordSet.")
    # Recursively returns the parent's the parent.
    return _find_record_set(graph, parent_node)


def _add_operations_for_field_with_source(
    issues: Issues,
    graph: nx.MultiDiGraph,
    operations: nx.MultiDiGraph,
    last_operation: Mapping[Node, Operation],
    node: Field,
    rdf_namespace_manager: namespace.NamespaceManager,
):
    """Adds all operations for a node of type `Field`.

    Operations are:

    - `Join` if the field comes from several sources.
    - `ReadField` to specify how the field is read.
    - `GroupRecordSet` to structure the final dict that is sent back to the user.
    """
    # Attach the field to a record set
    record_set = _find_record_set(graph, node)
    group_record_set = GroupRecordSet(node=record_set)
    parent_node = graph.nodes[node].get("parent")
    join = Join(node=parent_node)
    # `Join()` takes left=Source and right=Source as kwargs.
    if node.references is not None and len(node.references.reference) > 1:
        kwargs = {
            "left": node.source,
            "right": node.references,
        }
        operations.add_node(join, kwargs=kwargs)
    else:
        # Else, we add a dummy JOIN operation.
        operations.add_node(join)
    operations.add_edge(join, group_record_set)
    for predecessor in graph.predecessors(node):
        operations.add_edge(last_operation[predecessor], join)
    if len(node.source.reference) != 2:
        issues.add_error(f'Wrong source in node "{node.uid}"')
        return
    # Read/extract the field
    read_field = ReadField(node=node, rdf_namespace_manager=rdf_namespace_manager)
    operations.add_edge(group_record_set, read_field)
    last_operation[node] = read_field


def _add_operations_for_field_with_data(
    graph: nx.MultiDiGraph,
    operations: nx.MultiDiGraph,
    last_operation: Mapping[Node, Operation],
    node: Field,
):
    """Adds a `Data` operation for a node of type `Field` with data.

    Those nodes return a DataFrame representing the lines in `data`.
    """
    operation = Data(node=node)
    for predecessor in graph.predecessors(node):
        operations.add_edge(last_operation[predecessor], operation)
    last_operation[node] = operation


def _add_operations_for_file_object(
    graph: nx.MultiDiGraph,
    operations: nx.MultiDiGraph,
    last_operation: Mapping[Node, Operation],
    node: Node,
    croissant_folder: epath.Path,
):
    """Adds all operations for a node of type `FileObject`.

    Operations are:

    - `Download`.
    - `Untar` if the file needs to be extracted.
    - `Merge` to merge several dataframes into one.
    - `ReadCsv` to read the file if it's a CSV.
    """
    # Download the file
    operation = Download(node=node, url=node.content_url)
    operations.add_node(operation)
    for successor in graph.successors(node):
        # Extract the file if needed
        if (
            node.encoding_format == "application/x-tar"
            and isinstance(successor, (FileObject, FileSet))
            and successor.encoding_format != "application/x-tar"
        ):
            untar = Untar(node=node, target_node=successor)
            operations.add_edge(operation, untar)
            last_operation[node] = untar
            operation = untar
        if isinstance(successor, FileSet):
            merge = Merge(node=successor)
            operations.add_edge(operation, merge)
            operation = merge
    # Read the file
    if node.encoding_format == "text/csv":
        read_csv = ReadCsv(
            node=node,
            url=node.content_url,
            croissant_folder=croissant_folder,
        )
        operations.add_edge(operation, read_csv)
        operation = read_csv
    last_operation[node] = operation


@dataclasses.dataclass(frozen=True)
class ComputationGraph:
    """Graph of dependent operations to execute to generate the dataset."""

    issues: Issues
    graph: nx.MultiDiGraph

    @classmethod
    def from_nodes(
        cls,
        issues: Issues,
        metadata: Node,
        graph: nx.MultiDiGraph,
        croissant_folder: epath.Path,
        rdf_namespace_manager: namespace.NamespaceManager,
    ) -> "ComputationGraph":
        """Builds the ComputationGraph from the nodes.

        This is done by:

        1. Building the structure graph.
        2. Building the computation graph by exploring the structure graph layers by
        layers in a breadth-first search.
        """
        last_operation: Mapping[Node, Operation] = {}
        operations = nx.MultiDiGraph()
        # Find all fields
        for node in nx.topological_sort(graph):
            predecessors = graph.predecessors(node)
            # Transfer operation from predecessor -> node.
            for predecessor in predecessors:
                if predecessor in last_operation:
                    last_operation[node] = last_operation[predecessor]
            if isinstance(node, Field):
                if node.source and not node.has_sub_fields:
                    _add_operations_for_field_with_source(
                        issues,
                        graph,
                        operations,
                        last_operation,
                        node,
                        rdf_namespace_manager,
                    )
                elif node.data:
                    _add_operations_for_field_with_data(
                        graph,
                        operations,
                        last_operation,
                        node,
                    )
            elif isinstance(node, FileObject):
                _add_operations_for_file_object(
                    graph, operations, last_operation, node, croissant_folder
                )

        # Attach all entry nodes to a single `start` node
        entry_operations = get_entry_nodes(issues, operations)
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


def get_entry_nodes(issues: Issues, graph: nx.MultiDiGraph) -> list[Node]:
    """Retrieves the entry nodes (without predecessors) in a graph."""
    entry_nodes = []
    for node, indegree in graph.in_degree(graph.nodes()):
        if indegree == 0:
            entry_nodes.append(node)
    # Fields should usually not be entry nodes, except if they have subFields. So we
    # check for this:
    for node in entry_nodes:
        if isinstance(node, Field) and not node.has_sub_fields:
            issues.add_error(
                f'Node "{node.uid}" is a field and has no source. Please, use'
                f" {constants.ML_COMMONS_SOURCE} to specify the source."
            )
    return entry_nodes


def _check_no_duplicate(issues: Issues, nodes: list[Node]) -> Mapping[str, Node]:
    """Checks that no node has duplicated UID and returns the mapping `uid`->`Node`."""
    uid_to_node: Mapping[str, Node] = {}
    for node in nodes:
        if node.uid in uid_to_node:
            issues.add_error(f"Duplicate node with the same identifier: {node.uid}")
        uid_to_node[node.uid] = node
    return uid_to_node


def add_node_as_entry_node(issues: Issues, graph: nx.MultiDiGraph, node: Node):
    """Add `node` as the entry node of the graph by updating `graph` in place."""
    graph.add_node(node, parent=None)
    entry_nodes = get_entry_nodes(issues, graph)
    for entry_node in entry_nodes:
        if isinstance(node, (FileObject, FileSet)):
            graph.add_edge(entry_node, node)


def add_edge(
    issues: Issues,
    graph: nx.MultiDiGraph,
    uid_to_node: Mapping[str, Node],
    uid: str,
    node: Node,
    expected_types: type | tuple[type],
):
    if uid not in uid_to_node:
        issues.add_error(
            f'There is a reference to node named "{uid}" in node "{node.uid}", but this'
            " node doesn't exist."
        )
        return
    if not isinstance(uid_to_node[uid], expected_types):
        issues.add_error(
            f'There is a reference to node named "{uid}" in node "{node.uid}", but this'
            f" node doesn't have the expected type: {expected_types}."
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
                add_edge(issues, graph, uid_to_node, uid, node, (FileObject, FileSet))
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
                    # Record sets are not valid parents here.
                    # The case can arise when a Field references a record set to have a
                    # machine-readable explanation of the field (see datasets/titanic
                    # for example).
                    if not isinstance(uid_to_node[uid], RecordSet):
                        add_edge(issues, graph, uid_to_node, uid, node, Node)
                # ...or the source can be a metadata.
                elif (uid := reference[0]) in uid_to_node:
                    if not isinstance(uid_to_node[uid], RecordSet):
                        add_edge(
                            issues, graph, uid_to_node, uid, node, (FileObject, FileSet)
                        )
                else:
                    issues.add_error(
                        "Source refers to an unknown node"
                        f' "{concatenate_uid(reference)}".'
                    )
        # Other nodes
        elif node.parent_uid is not None:
            add_edge(issues, graph, uid_to_node, node.parent_uid, node, Node)
    # `Metadata` are used as the entry node.
    metadata = next((node for node in nodes if isinstance(node, Metadata)), None)
    if metadata is None:
        issues.add_error("No metadata is defined in the dataset.")
        return None, graph
    add_node_as_entry_node(issues, graph, metadata)
    if not graph.is_directed():
        issues.add_error("Structure graph is not directed.")
    return metadata, graph
