"""concatenate_test module."""

from mlcroissant._src.operation_graph.operations import concatenate
from mlcroissant._src.tests.nodes import empty_file_set
from mlcroissant._src.tests.operations import operations


def test_str_representation():
    operation = concatenate.Concatenate(operations=operations(), node=empty_file_set)
    assert str(operation) == "Concatenate(file_set_name)"
