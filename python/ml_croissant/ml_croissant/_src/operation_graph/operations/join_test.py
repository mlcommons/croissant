"""join_test module."""

from ml_croissant._src.operation_graph.operations import join
from ml_croissant._src.tests.nodes import empty_record_set


def test_str_representation():
    operation = join.Join(node=empty_record_set)
    assert str(operation) == "Join(record_set_name)"
