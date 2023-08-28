"""download_test module."""

from unittest import mock

import networkx as nx
import pytest

from ml_croissant._src.operation_graph.operations import Data
from ml_croissant._src.operation_graph.operations.download import Download
from ml_croissant._src.operation_graph.operations.download import execute_downloads
from ml_croissant._src.operation_graph.operations.download import extract_git_info
from ml_croissant._src.operation_graph.operations.download import insert_credentials
from ml_croissant._src.tests.nodes import create_test_file_object
from ml_croissant._src.tests.nodes import empty_file_object
from ml_croissant._src.tests.nodes import empty_record_set


def test_str_representation():
    operation = Download(node=empty_file_object, url="http://mlcommons.org")
    assert str(operation) == "Download(file_object_name)"


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


def test_extract_git_info():
    with pytest.raises(ValueError, match="unknown git host"):
        extract_git_info("https://github.com/mlcommons/croissant")

    assert extract_git_info("https://huggingface.co/datasets/mnist") == (
        "https://huggingface.co/datasets/mnist",
        None,
    )
    assert extract_git_info("https://huggingface.co/datasets/mlcommons/mnist") == (
        "https://huggingface.co/datasets/mlcommons/mnist",
        None,
    )
    assert extract_git_info(
        "https://huggingface.co/datasets/mnist/tree/refs%2Fconvert%2Fparquet"
    ) == ("https://huggingface.co/datasets/mnist", "refs/convert/parquet")
    assert extract_git_info(
        "https://huggingface.co/datasets/mlcommons/mnist/tree/refs%2Fconvert%2Fparquet"
    ) == ("https://huggingface.co/datasets/mlcommons/mnist", "refs/convert/parquet")


def test_insert_credentials():
    assert (
        insert_credentials(
            "https://github.com/mlcommons/croissant", username=None, password=None
        )
        == "https://github.com/mlcommons/croissant"
    )
    assert (
        insert_credentials(
            "https://github.com/mlcommons/croissant",
            username="username@mlcommons.com",
            password="my/password",
        )
        == "https://username%40mlcommons.com:my/password@github.com/mlcommons/croissant"
    )
    with pytest.raises(ValueError, match="provide both"):
        insert_credentials(
            "https://github.com/mlcommons/croissant",
            username="username@mlcommons.com",
            password=None,
        )
    with pytest.raises(ValueError, match="provide both"):
        insert_credentials(
            "https://github.com/mlcommons/croissant",
            username=None,
            password="my/password",
        )
