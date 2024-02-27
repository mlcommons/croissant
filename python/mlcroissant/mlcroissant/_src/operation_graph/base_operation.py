"""Base operation module."""

from __future__ import annotations

import abc
import dataclasses
from typing import Iterable

import networkx as nx

from mlcroissant._src.structure_graph.base_node import Node


class Operations(nx.DiGraph):
    """Overwrites nx.DiGraph to keep track of operations.

    `self.last_operations` maintains a pointer to the chain of last operations for each
    node.
    """

    def __init__(self):
        """Initializes `self.last_operations`."""
        super().__init__(self)
        self.last_operations: dict[Node, Operation] = {}

    def add_node(self, operation: Operation) -> None:
        """Overloads nx.add_node to keep track of the last operations."""
        if not self.has_node(operation):
            super().add_node(operation)

    def add_edge(self, operation1: Operation, operation2: Operation) -> None:
        """Overloads nx.add_node to keep track of the last operations."""
        if not self.has_edge(operation1, operation2):
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
        self.connect_to_last_operation(self.node)
        self.set_last_operation_for(self.node)

    def set_last_operation_for(self, node: Node):
        """Sets self as the last operation for the node and its successors."""
        self.operations.last_operations[node] = self
        for successor in node.successors:
            # Report the last operation to the next node in the graph.
            self.operations.last_operations[successor] = self

    def connect_to_last_operation(self, node: Node):
        """Connects the current operation (self) to the last operation for node."""
        # The previous operation can be indexed either on the node itself...
        if node in self.operations.last_operations:
            previous_operation = self.operations.last_operations[node]
            if previous_operation != self:
                self.operations.add_edge(previous_operation, self)
        # ...or the node's predecessor.
        elif node.predecessor in self.operations.last_operations:
            previous_operation = self.operations.last_operations[node.predecessor]
            if previous_operation != self:
                self.operations.add_edge(previous_operation, self)

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        """Abstract method to implement when an operation is called."""
        raise NotImplementedError

    def __repr__(self):
        """Prints a simplified string representation of the operation."""
        return f"{type(self).__name__}({self.node.uuid})"

    def __rrshift__(
        self, left_operations: Operation | list[Operation] | None
    ) -> Operation:
        """Allows to chain operations in their graph: `operation1 >> operation2`."""
        right_operation = self
        if isinstance(left_operations, Operation):
            left_operations = [left_operations]
        elif left_operations is None:
            left_operations = []
        for left_operation in left_operations:
            self.operations.add_edge(left_operation, right_operation)
        return right_operation
