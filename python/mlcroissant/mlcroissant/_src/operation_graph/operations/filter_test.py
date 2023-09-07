"""filter_test module."""

from mlcroissant._src.operation_graph.operations.filter import FilterFiles
from mlcroissant._src.tests.nodes import empty_file_set


def test_str_representation():
    operation = FilterFiles(node=empty_file_set)
    assert str(operation) == "FilterFiles(file_set_name)"
