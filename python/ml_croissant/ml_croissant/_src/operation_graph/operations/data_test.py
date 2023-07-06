"""data_test module."""

from ml_croissant._src.operation_graph.operations import data
from ml_croissant._src.tests.nodes import empty_node


def test_str_representation():
    operation = data.Data(node=empty_node)
    assert str(operation) == "Data(node_name)"
