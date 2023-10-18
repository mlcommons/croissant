"""Tests for execute."""

from unittest import mock

import networkx as nx

from mlcroissant._src.operation_graph.execute import execute_downloads
from mlcroissant._src.operation_graph.operations import Data
from mlcroissant._src.operation_graph.operations.download import Download
from mlcroissant._src.tests.nodes import create_test_file_object
from mlcroissant._src.tests.nodes import empty_record_set


def test_execute_downloads():
    operations = nx.DiGraph()
    node1 = create_test_file_object(name="node1")
    node2 = create_test_file_object(name="node2")
    download1 = Download(operations=operations, node=node1)
    download2 = Download(operations=operations, node=node2)
    data = Data(operations=operations, node=empty_record_set)
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
