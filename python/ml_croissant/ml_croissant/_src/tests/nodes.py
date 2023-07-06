"""Testing utils for `Node`."""

from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.base_node import Node


class _EmptyNode(Node):
    def check(self):
        pass


empty_node = _EmptyNode(
    issues=Issues(),
    graph=None,
    node=None,
    name="node_name",
    uid="node_name",
)
