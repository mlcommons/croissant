"""Base operation module."""

from __future__ import annotations

import abc
import dataclasses
import types
from typing import Any, Generic, Iterable, Sequence, TypeVar

import networkx as nx
import pandas as pd

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

    # pytype: disable=signature-mismatch
    def predecessors(self, operation: Operation) -> Iterable[Operation]:
        """Overloads nx.predecessors to have types."""
        return super().predecessors(operation)

    # pytype: enable=signature-mismatch

    @property
    def nodes(self) -> Iterable[Operation]:
        """Overloads nx.nodes to return an interator of operations."""
        return super().nodes()

    def entry_operations(self) -> Sequence[Operation]:
        """Lists all operations without a parent in the graph of operations."""
        return [
            operation
            for operation, indegree in self.in_degree(self.nodes)
            if indegree == 0 and isinstance(operation, Operation)
        ]


OutputT = TypeVar("OutputT")


@dataclasses.dataclass(frozen=True, repr=False)
class Operation(abc.ABC, Generic[OutputT]):
    """Generic base class to define an operation.

    `@dataclass(frozen=True)` allows having a hashable operation for NetworkX to use
    operations as nodes of  graphs.

    `@dataclass(repr=False)` allows having a readable stringified `str(operation)`.

    `_output` is an internal-only field used to cache the output of calling the
    operation (`self.call()`).

    Args:
        operations: The graph of all operations.
        node: The node attached to the operation for the context.
    """

    operations: Operations
    node: Node
    _output: OutputT = dataclasses.field(init=False, hash=False, compare=False)

    def __post_init__(self):
        """Adds the operation to the graph of operations."""
        operation = self
        # If the operation is already in the graph we don't want to leak other
        # references to the same operation, so we find the original operation:
        if self in self.operations:
            operation = next(
                operation for operation in self.operations if operation == self
            )
        operation.operations.add_node(operation)
        operation.connect_to_last_operation(operation.node)
        operation.set_last_operation_for(operation.node)

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

    def __call__(self, set_output_in_memory: bool = False) -> OutputT:
        """Executes the current operation from the output of its parents and store the result."""
        if self.has_output():
            return self._output
        inputs = self.inputs
        output = self.call() if inputs is None else self.call(*inputs)
        if isinstance(output, types.GeneratorType) and set_output_in_memory:
            output = pd.DataFrame(output)  # type:ignore
        self.set_output(output)
        return output

    @abc.abstractmethod
    def call(self, *args, **kwargs) -> OutputT:
        """Abstract method to implement when an operation is called."""
        raise NotImplementedError

    @property
    def inputs(self) -> Sequence[Any]:
        """Returns the inputs of the operation - i.e. the outputs of the predecessors."""
        inputs = []
        parents = self.operations.predecessors(self)
        for parent in parents:
            if not parent.has_output():
                raise ValueError(
                    f'did not set output for "{parent}". This situation should not'
                    " happen as we go through the graph in a topological sort."
                )
            inputs.append(parent._output)
        return inputs

    @property
    def output(self) -> OutputT:
        """Returns the cached output of the operation if it is set."""
        return self._output

    def has_output(self) -> bool:
        """Checks whether self.output was already set."""
        return hasattr(self, "_output")

    def set_output(self, output: OutputT):
        """Sets the given output."""
        object.__setattr__(self, "_output", output)

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

    def __reduce__(self):
        """Allows pickling the operation.

        `self.operations` is stored separately in the state to break the cyclic
        reference between Operation and Operations. We could refactor the codebase to
        not have this dependency, but it would be a bigger change and it's convenient
        to be able to reference all operations from a single operation.
        """
        state = self.__getstate__()
        state_setter = {"operations": self.operations}
        if "_output" in state:
            state_setter["_output"] = state.pop("_output")
        args = tuple(state.values())
        return (
            self.__class__,
            args,
            state_setter,
        )

    def __getstate__(self):
        """Overwrites __getstate__ for pickling."""
        state = {}
        for field in dataclasses.fields(self):
            if field.name == "operations":
                state[field.name] = Operations()
            elif hasattr(self, field.name):  # _output may not be set
                state[field.name] = getattr(self, field.name)
        return state

    def __setstate__(self, state):
        """Overwrites __setstate__ for pickling."""
        object.__setattr__(self, "operations", state["operations"])
        if "_output" in state:
            self.set_output(state["_output"])
