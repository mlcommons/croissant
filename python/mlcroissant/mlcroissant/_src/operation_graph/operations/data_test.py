"""data_test module."""

from mlcroissant._src.operation_graph.operations import data
from mlcroissant._src.tests.nodes import empty_record_set
from mlcroissant._src.tests.operations import operations


def test_str_representation():
    operation = data.Data(operations=operations(), node=empty_record_set)
    assert str(operation) == "Data(record_set_name)"
