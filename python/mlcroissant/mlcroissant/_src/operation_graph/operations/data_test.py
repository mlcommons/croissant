"""data_test module."""

from mlcroissant._src.operation_graph.operations import data
from mlcroissant._src.tests.nodes import empty_record_set


def test_str_representation():
    operation = data.Data(node=empty_record_set)
    assert str(operation) == "Data(record_set_name)"
