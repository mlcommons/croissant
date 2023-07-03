"""extract_test module."""

from ml_croissant._src.operation_graph.operations import extract
from ml_croissant._src.tests.nodes import empty_node


def test_str_representation():
    operation = extract.Untar(node=empty_node, target_node=empty_node)
    assert str(operation) == "Untar(node_name)"
