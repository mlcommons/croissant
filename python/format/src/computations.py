"""computations module."""

import dataclasses
from typing import Mapping

import networkx as nx

from format.src.errors import Issues
from format.src.nodes import (
    concatenate_uid,
    Field,
    FileObject,
    FileSet,
    Metadata,
    Node,
    RecordSet,
)


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
        elif isinstance(node, Field) and node.source:
            reference = node.source.reference
            # The source can be either another field...
            if (uid := concatenate_uid(reference)) in uid_to_node:
                add_edge(issues, graph, uid_to_node, uid, node)
            # ...or the source can be a metadata.
            elif (uid := reference[0]) in uid_to_node:
                add_edge(issues, graph, uid_to_node, uid, node)
            else:
                issues.add_error(
                    f'Source refers to an unknown node "{concatenate_uid(reference)}".'
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
    return metadata, graph


@dataclasses.dataclass(frozen=True)
class Operation:
    name: str


@dataclasses.dataclass(frozen=True)
class ComputationGraph:
    """Graph of dependent operations to execute to generate the dataset."""

    issues: Issues
    graph: nx.MultiDiGraph

    @classmethod
    def from_nodes(cls, issues: Issues, nodes: list[Node]) -> "ComputationGraph":
        """Builds the ComputationGraph from the nodes.

        This is done by:

        1. Building the structure graph.
        2. Building the computation graph by exploring the structure graph layers by
        layers in a breadth-first search.
        """
        entry_node, graph = build_structure_graph(issues, nodes)
        if not graph.is_directed():
            issues.add_error("Final graph is not directed.")
        last_operation_for_node: Mapping[Node, Operation] = {}
        operations = nx.MultiDiGraph()
        for layer in nx.bfs_layers(graph, entry_node):
            for node in layer:
                predecessors = graph.predecessors(node)
                for predecessor in predecessors:
                    if predecessor in last_operation_for_node:
                        last_operation_for_node[node] = last_operation_for_node[
                            predecessor
                        ]
                if isinstance(node, Field):
                    if node.source and not node.has_sub_fields:
                        if len(node.source.reference) != 2:
                            issues.add_error(f'Wrong source in node "{node.uid}"')
                            continue
                        predecessor = next(graph.predecessors(node))
                        operation = Operation(f"field:{node.name}")
                        operations.add_edge(
                            last_operation_for_node[predecessor], operation
                        )
                        if node.source.apply_transform_regex:
                            new_operation = Operation("transform-regex")
                            operations.add_edge(operation, new_operation)
                            operation = new_operation
                        if node.source.apply_transform_separator:
                            new_operation = Operation("transform-separator")
                            operations.add_edge(operation, new_operation)
                            operation = new_operation
                        last_operation_for_node[node] = operation
                        parent_node = graph.nodes[node].get("parent")
                        if isinstance(parent_node, Field) and isinstance(node, Field):
                            new_operation = Operation(f"field:{parent_node.uid}")
                            operations.add_edge(operation, new_operation)
                            operation = new_operation
                            last_operation_for_node[parent_node] = new_operation
                            parent_node = graph.nodes[parent_node].get("parent")
                        if isinstance(parent_node, RecordSet):
                            new_operation = Operation(f"record-set:{parent_node.uid}")
                            operations.add_edge(operation, new_operation)
                            operation = new_operation
                            last_operation_for_node[parent_node] = new_operation
                elif isinstance(node, FileObject):
                    operation = Operation(name=f"download:{node.uid}")
                    operations.add_node(operation)
                    last_operation_for_node[node] = operation
                    for successor in graph.successors(node):
                        if (
                            node.encoding_format == "application/x-tar"
                            and isinstance(successor, (FileObject, FileSet))
                            and successor.encoding_format != "application/x-tar"
                        ):
                            operation = Operation(name=f"extract:{node.uid}")
                            operations.add_edge(
                                last_operation_for_node[node], operation
                            )
                            last_operation_for_node[node] = operation
                elif isinstance(node, FileSet):
                    if node.contained_in:
                        operation = Operation(name=f"filter:{node.uid}")
                        for source in graph.predecessors(node):
                            operations.add_edge(
                                last_operation_for_node[source], operation
                            )
                            last_operation_for_node[source] = operation
                        last_operation_for_node[node] = operation

        # Attach all entry nodes to a single `start` node
        entry_operations = get_entry_nodes(operations)
        init_operation = Operation("init")
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
