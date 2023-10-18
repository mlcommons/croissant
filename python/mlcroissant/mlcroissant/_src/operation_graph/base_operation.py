"""Base operation module."""

import abc
import dataclasses

import networkx as nx

from mlcroissant._src.structure_graph.base_node import Node


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

    operations: nx.DiGraph
    node: Node

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        """Abstract method to implement when an operation is called."""
        raise NotImplementedError

    def __repr__(self):
        """Prints a simplified string representation of the operation."""
        return f"{type(self).__name__}({self.node.uid})"
