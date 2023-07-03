"""download_test module."""

from ml_croissant._src.operation_graph.operations import download
from ml_croissant._src.tests.nodes import empty_node


def test_str_representation():
    operation = download.Download(node=empty_node, url="http://mlcommons.org")
    assert str(operation) == "Download(node_name)"
