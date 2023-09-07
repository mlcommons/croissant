"""init_test module."""

from mlcroissant._src.operation_graph.operations import init
from mlcroissant._src.tests.nodes import empty_node


def test_str_representation():
    operation = init.InitOperation(node=empty_node)
    assert str(operation) == "InitOperation(node_name)"
