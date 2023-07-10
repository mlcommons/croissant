"""extract_test module."""

from ml_croissant._src.operation_graph.operations import extract
from ml_croissant._src.tests.nodes import empty_file_object, empty_file_set


def test_str_representation():
    operation = extract.Untar(node=empty_file_object, target_node=empty_file_set)
    assert str(operation) == "Untar(file_object_name)"
