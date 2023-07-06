"""merge_test module."""

from ml_croissant._src.operation_graph.operations import merge
from ml_croissant._src.tests.nodes import empty_node


def test_str_representation():
    operation = merge.Merge(node=empty_node)
    assert str(operation) == "Merge(node_name)"
