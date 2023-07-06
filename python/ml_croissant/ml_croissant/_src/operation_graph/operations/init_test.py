"""init_test module."""

from ml_croissant._src.operation_graph.operations import init
from ml_croissant._src.tests.nodes import empty_node


def test_str_representation():
    operation = init.InitOperation(node=empty_node)
    assert str(operation) == "InitOperation(node_name)"
