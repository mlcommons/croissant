"""Testing utils for `Node`."""

from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.nodes import Field, FileObject, FileSet


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

empty_field = Field(
    issues=Issues(),
    graph=None,
    node=None,
    name="field_name",
    uid="field_name",
)

empty_file_object = FileObject(
    issues=Issues(),
    graph=None,
    node=None,
    name="file_object_name",
    uid="file_object_name",
)

empty_file_set = FileSet(
    issues=Issues(),
    graph=None,
    node=None,
    name="file_set_name",
    uid="file_set_name",
)
