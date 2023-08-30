"""Tests for execute."""

from unittest import mock

import networkx as nx

from ml_croissant._src.operation_graph.execute import execute_downloads
from ml_croissant._src.operation_graph.operations import Data
from ml_croissant._src.operation_graph.operations.download import Download
from ml_croissant._src.tests.nodes import create_test_file_object
from ml_croissant._src.tests.nodes import empty_record_set


def test_execute_downloads():
    operations = nx.MultiDiGraph()
    node1 = create_test_file_object(name="node1")
    node2 = create_test_file_object(name="node2")
    download1 = Download(node=node1, url="http://mlcommons.org")
    download2 = Download(node=node2, url="http://mlcommons.org")
    data = Data(node=empty_record_set)
    operations.add_node(download1)
    operations.add_node(download2)
    operations.add_node(download2)
    operations.add_node(data)
    with mock.patch.object(Download, "__call__") as download_call, mock.patch.object(
        Data, "__call__"
    ) as data_call:
        execute_downloads(operations)
        assert download_call.call_count == 2
        data_call.assert_not_called()
