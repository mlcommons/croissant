"""download_test module."""

import pytest
from typing import TypeVar
import hashlib
import requests
import tempfile

from mlcroissant._src.operation_graph.operations.download import Download
from mlcroissant._src.operation_graph.operations.download import extract_git_info
from mlcroissant._src.operation_graph.operations.download import insert_credentials
from mlcroissant._src.operation_graph.operations.download import _get_hash_obj
from mlcroissant._src.tests.nodes import empty_file_object, create_test_file_set, create_test_node
from mlcroissant._src.structure_graph.nodes.file_set import FileSet
from mlcroissant._src.structure_graph.nodes.file_object import FileObject


def test_str_representation():
    operation = Download(node=empty_file_object, url="http://mlcommons.org")
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
    file_object = FileObject(
            md5="12345",
        )
    hash_obj = _get_hash_obj(file_object)

    assert isinstance(hash_obj, type(hashlib.md5()))

def test_get_hash_obj_sha256():
    file_object = FileObject(
            sha256="12345",
        )
    hash_obj = _get_hash_obj(file_object)

    assert isinstance(hash_obj, type(hashlib.sha256()))

def test_checking_hash_correctly():
    url = "https://www.openml.org/data/get_csv/16826755/phpMYEkMl"
    file_object = FileObject(
            sha256="c617db2c7470716250f6f001be51304c76bcc8815527ab8bae734bdca0735737",
        )
    
    hash = _get_hash_obj(file_object)

    response = requests.get(url, stream=True, timeout=10)
    total = int(response.headers.get("Content-Length", 0))
    with tempfile.TemporaryFile() as file:
            for data in response.iter_content(chunk_size=1024):
                size = file.write(data)
                hash.update(data)

    downloaded_file_hash = hash.hexdigest()

    assert (downloaded_file_hash) == (getattr(file_object, hash.name))