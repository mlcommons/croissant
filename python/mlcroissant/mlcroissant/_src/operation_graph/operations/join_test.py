"""join_test module."""

from mlcroissant._src.operation_graph.operations import join
from mlcroissant._src.tests.nodes import empty_record_set


def test_str_representation():
    operation = join.Join(node=empty_record_set)
    assert str(operation) == "Join(record_set_name)"
