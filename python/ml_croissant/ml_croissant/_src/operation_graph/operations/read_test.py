"""read_test module."""

from etils import epath
from ml_croissant._src.operation_graph.operations import read
from ml_croissant._src.tests.nodes import empty_node


def test_str_representation():
    operation = read.ReadCsv(
        node=empty_node, folder=epath.Path(), url="http://mlcommons.org"
    )
    assert str(operation) == "ReadCsv(node_name)"
