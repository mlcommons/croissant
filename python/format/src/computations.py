import dataclasses
from typing import Mapping

import networkx as nx

from format.src import graphs_utils
from format.src.errors import Issues
from format.src.nodes import (
    Field,
    FileObject,
    FileSet,
    Node,
    RecordSet,
)


def get_structure_graph(nodes: list[Node]) -> nx.MultiDiGraph():
    graph = nx.MultiDiGraph()
    for node in nodes:
        graph.add_node(node.name, node=node)
        if node.sources:
            for source in node.sources:
                graph.add_edge(source[0], node.name)
        elif node.parent_name is not None:
            graph.add_edge(node.parent_name, node.name)
    entry_nodes = [
        graph.nodes[node]["node"]
        for node, indegree in graph.in_degree(graph.nodes())
        if indegree == 0
    ]
    for node in entry_nodes:
        if isinstance(node, (FileObject, FileSet)):
            graph.add_edge(node.parent_name, node.name)
    return graph


@dataclasses.dataclass(frozen=True)
class Operation:
    name: str


@dataclasses.dataclass(frozen=True)
class ComputationGraph:
    issues: Issues
    graph: nx.MultiDiGraph

    @classmethod
    def from_nodes(self, issues: Issues, nodes: list[Node]) -> "ComputationGraph":
        graph = get_structure_graph(nodes)
        if not graph.is_directed():
            issues.add_error("Final graph is not directed.")
        last_operation_for_node: Mapping[str, Operation] = {}
        graphs_utils.pretty_print_graph(graph)
        operations = nx.MultiDiGraph()
        entry_nodes = [
            node_name
            for node_name, indegree in graph.in_degree(graph.nodes())
            if indegree == 0
        ]
        if len(entry_nodes) != 1:
            issues.add_error(f"The structure graph has {len(entry_nodes)}. Expected 1.")
        for layer in nx.bfs_layers(graph, entry_nodes[0]):
            for node_name in layer:
                node = graph.nodes[node_name]["node"]
                predecessors = graph.predecessors(node_name)
                for predecessor in predecessors:
                    if predecessor in last_operation_for_node:
                        last_operation_for_node[node.name] = last_operation_for_node[
                            predecessor
                        ]
                if isinstance(node, Field):
                    if node.sources:
                        for source in node.sources:
                            if len(source) != 2:
                                issues.add_error(f'Wrong source in node "{node.name}"')
                                continue
                            source_name, field = source
                            operation_name = (
                                "field" if isinstance(node, Field) else "subField"
                            )
                            operation = Operation(f"{operation_name}:{field}")
                            operations.add_edge(
                                last_operation_for_node[source_name], operation
                            )
                            if node.source.apply_transform_regex:
                                new_operation = Operation("transform-regex")
                                operations.add_edge(operation, new_operation)
                                operation = new_operation
                            if node.source.apply_transform_separator:
                                new_operation = Operation("transform-separator")
                                operations.add_edge(operation, new_operation)
                                operation = new_operation
                            # TODO(marcenacp): Should keep the recursion?
                            parent_node = graph.nodes[node.parent_name]["node"]
                            if isinstance(parent_node, Field) and isinstance(
                                node, Field
                            ):
                                new_operation = Operation(f"field:{parent_node.name}")
                                operations.add_edge(operation, new_operation)
                                operation = new_operation
                                node = parent_node
                            parent_node = graph.nodes[node.parent_name]["node"]
                            if isinstance(parent_node, RecordSet):
                                new_operation = Operation(
                                    f"record-set:{parent_node.name}"
                                )
                                operations.add_edge(operation, new_operation)
                                operation = new_operation
                elif isinstance(node, FileObject):
                    operation = Operation(name=f"download:{node.name}")
                    operations.add_node(operation)
                    last_operation_for_node[node.name] = operation
                    next_node_name = next(graph.neighbors(node_name))
                    next_node = graph.nodes[next_node_name]["node"]
                    if (
                        node.encoding_format == "application/x-tar"
                        and isinstance(next_node, (FileObject, FileSet))
                        and next_node.encoding_format != "application/x-tar"
                    ):
                        operation = Operation(name=f"extract:{node.name}")
                        operations.add_edge(
                            last_operation_for_node[node.name], operation
                        )
                        last_operation_for_node[node.name] = operation
                elif isinstance(node, (FileObject, FileSet)):
                    if node.sources:
                        operation = Operation(name=f"filter:{node.name}")
                        for source in node.sources:
                            operations.add_edge(
                                last_operation_for_node[source[0]], operation
                            )
                            last_operation_for_node[source[0]] = operation
                        last_operation_for_node[node.name] = operation

        # Attach all entry nodes to a single `start` node
        entry_operations = [
            operation
            for operation, indegree in operations.in_degree(operations.nodes())
            if indegree == 0
        ]
        empty_operation = Operation("init")
        for entry_operation in entry_operations:
            operations.add_edge(empty_operation, entry_operation)

        return ComputationGraph(issues=issues, graph=operations)

    def check_graph(self):
        if not self.graph.is_directed():
            self.issues.add_error("Computation graph is not directed.")
        selfloops = [operation.name for operation, _ in nx.selfloop_edges(self.graph)]
        if selfloops:
            self.issues.add_error(
                f"The following operations refered to themselves: {selfloops}"
            )
