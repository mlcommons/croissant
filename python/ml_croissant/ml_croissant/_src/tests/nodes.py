"""Testing utils for `Node`."""

from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.base_node import Node

empty_node = Node(
    issues=Issues(),
    graph=None,
    node=None,
    name="node_name",
    parent_uid="parent_name",
)
