"""Base operation module."""

from __future__ import annotations

import abc
import dataclasses
from typing import Iterable

import networkx as nx

from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet


class Operations(nx.DiGraph):
    """Overwrites nx.DiGraph to keep track of last operations."""

    def last_operations(self, node: Node, only_leaf=False) -> list[Operation]:
        """Retrieves the last operations for a node in the graph of operations.

        Args:
            node: The node of the operations.
            only_leaf: Whether to only pick leaves operations (only_leaf=True) or to
                visit upstream operations (only_leaf=False).
        """
        leaves = [operation for operation in self.nodes if self.is_leaf(operation)]

        def is_ancestor(node1: Node, node2: Node) -> bool:
            # node1 is predecessor of node2 iff node2 is in the descendants of node1.
            ancestors = nx.ancestors(node2.ctx.graph, node2)
            if isinstance(node1, RecordSet):
                # If node1 is a RecordSet, we have to inspect its fields.
                return any(is_ancestor(field1, node2) for field1 in node1.fields)
            return node1 in ancestors

        entry = self.entry_operations()[0]
        operations: set[Operation] = set()
        for leaf in leaves:
            if is_ancestor(leaf.node, node):
                operations.add(leaf)
            elif not only_leaf:
                # We explore upstream operations until we find the first operation that
                # matches the node.
                try:
                    for operation in reversed(
                        list(nx.shortest_path(self, entry, leaf))
                    ):
                        if is_ancestor(operation.node, node):
                            operations.add(operation)
                            break
                except nx.exception.NetworkXNoPath:
                    continue
        return list(operations)

    def add_node(self, operation: Operation) -> None:
        """Overloads nx.add_node to keep track of the last operations."""
        super().add_node(operation)

    def add_edge(self, operation1: Operation, operation2: Operation) -> None:
        """Overloads nx.add_node to keep track of the last operations."""
        super().add_edge(operation1, operation2)

    @property
    def nodes(self) -> Iterable[Operation]:
        """Overloads nx.nodes to return an interator of operations."""
        return super().nodes()

    def is_leaf(self, operation: Operation | None) -> bool:
        """Tests whether an operation is a leaf in the graph."""
        return self.out_degree(operation) == 0

    def entry_operations(self) -> list[Operation]:
        """Lists all operations without a parent in the graph of operations."""
        return [
            operation
            for operation, indegree in self.in_degree(self.nodes)
            if indegree == 0 and isinstance(operation, Operation)
        ]


@dataclasses.dataclass(frozen=True, repr=False)
class Operation(abc.ABC):
    """Generic base class to define an operation.

    `@dataclass(frozen=True)` allows having a hashable operation for NetworkX to use
    operations as nodes of  graphs.

    `@dataclass(repr=False)` allows having a readable stringified `str(operation)`.

    Args:
        node: The node attached to the operation for the context.
        output: The result of the operation when it is executed (as returned by
            __call__).
    """

    operations: Operations
    node: Node

    def __post_init__(self):
        """Adds the operation to the graph of operations."""
        self.operations.add_node(self)

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        """Abstract method to implement when an operation is called."""
        raise NotImplementedError

    def __repr__(self):
        """Prints a simplified string representation of the operation."""
        return f"{type(self).__name__}({self.node.uid})"

    def __rrshift__(self, left_operations: Operation | list[Operation]) -> Operation:
        """Allows to chain operations in their graph: `operation1 >> operation2`."""
        right_operation = self
        if isinstance(left_operations, Operation):
            left_operations = [left_operations]
        for left_operation in left_operations:
            self.operations.add_edge(left_operation, right_operation)
        return right_operation
