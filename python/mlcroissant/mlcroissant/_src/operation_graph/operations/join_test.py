"""join_test module."""

from mlcroissant._src.operation_graph.operations import join
from mlcroissant._src.tests.nodes import empty_record_set
from mlcroissant._src.tests.operations import operations


def test_str_representation():
    operation = join.Join(operations=operations(), node=empty_record_set)
    assert str(operation) == "Join(record_set_name)"
