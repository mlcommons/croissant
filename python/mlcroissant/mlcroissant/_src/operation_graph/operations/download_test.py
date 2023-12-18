"""download_test module."""

import hashlib

import pytest

from mlcroissant._src.operation_graph.operations.download import _get_hash_algorithm
from mlcroissant._src.operation_graph.operations.download import Download
from mlcroissant._src.operation_graph.operations.download import extract_git_info
from mlcroissant._src.operation_graph.operations.download import insert_credentials
from mlcroissant._src.structure_graph.nodes.file_object import FileObject
from mlcroissant._src.tests.nodes import empty_file_object
from mlcroissant._src.tests.operations import operations


def test_str_representation():
    operation = Download(operations=operations(), node=empty_file_object)
    assert str(operation) == "Download(file_object_name)"


def test_extract_git_info():
    with pytest.raises(ValueError, match="unknown git host"):
        extract_git_info("https://thisisnotagithost.com")

    assert extract_git_info("https://github.com/mlcommons/croissant") == (
        "https://github.com/mlcommons/croissant",
        None,
    )
    assert extract_git_info("https://gitlab.com/mlcommons/croissant") == (
        "https://gitlab.com/mlcommons/croissant",
        None,
    )
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


def test_get_hash_obj_md5():
    node = FileObject(
        md5="12345",
    )
    hash_algorithm = _get_hash_algorithm(node)

    assert isinstance(hash_algorithm, type(hashlib.md5()))


def test_get_hash_obj_sha256():
    node = FileObject(
        sha256="12345",
    )
    hash_algorithm = _get_hash_algorithm(node)

    assert isinstance(hash_algorithm, type(hashlib.sha256()))
