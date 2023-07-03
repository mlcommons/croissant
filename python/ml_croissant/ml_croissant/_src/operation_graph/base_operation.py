"""Base operation module."""

import dataclasses

from ml_croissant._src.structure_graph.base_node import Node


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

    def __call__(self, *args, **kwargs):
        raise NotImplementedError

    def __repr__(self):
        return f"{type(self).__name__}({self.node.uid})"
