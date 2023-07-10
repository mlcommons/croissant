"""merge_test module."""

from ml_croissant._src.operation_graph.operations import merge
from ml_croissant._src.tests.nodes import empty_file_set


def test_str_representation():
    operation = merge.Merge(node=empty_file_set)
    assert str(operation) == "Merge(file_set_name)"
