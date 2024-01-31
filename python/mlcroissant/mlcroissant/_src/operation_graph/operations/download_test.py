"""download_test module."""

import hashlib
import os
import tempfile

from etils import epath
import pytest

from mlcroissant._src.operation_graph.operations.download import _get_hash_algorithm
from mlcroissant._src.operation_graph.operations.download import Download
from mlcroissant._src.operation_graph.operations.download import extract_git_info
from mlcroissant._src.operation_graph.operations.download import get_download_filepath
from mlcroissant._src.operation_graph.operations.download import insert_credentials
from mlcroissant._src.structure_graph.nodes.croissant_version import CroissantVersion
from mlcroissant._src.structure_graph.nodes.file_object import FileObject
from mlcroissant._src.structure_graph.nodes.metadata import Metadata
from mlcroissant._src.tests.nodes import create_test_file_object
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


def test_get_download_filepath():
    # With mapping
    node = FileObject(
        name="foo",
        content_url="http://foo",
        sha256="12345",
        mapping={"foo": epath.Path("/bar/foo")},
    )
    assert get_download_filepath(node) == epath.Path("/bar/foo")

    # Without mapping
    node = FileObject(name="foo", content_url="http://foo", sha256="12345")
    assert os.fspath(get_download_filepath(node)).endswith(
        "download/croissant-0343a8f6b328d44bfe5b69437797bebc36c59c67ac6527fe1f14684142074fff"
    )


def test_hashes_do_not_match():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        filepath = f.name
        metadata = Metadata(name="bar", conforms_to=CroissantVersion.V_1_0)
        file_object = create_test_file_object(
            name="foo",
            content_url=os.fspath(filepath),
            # Hash won't match!
            sha256="12345",
        )
        file_object.parents = [metadata]
        download = Download(operations=operations(), node=file_object)
        with pytest.raises(ValueError, match="is not identical with the reference"):
            download()


@pytest.mark.parametrize("conforms_to", CroissantVersion)
def test_hashes_do_match(conforms_to):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        filepath = f.name
        metadata = Metadata(name="bar", conforms_to=conforms_to)
        file_object = create_test_file_object(
            name="foo",
            content_url=os.fspath(filepath),
            # Hash will match!
            sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
        file_object.parents = [metadata]
        download = Download(operations=operations(), node=file_object)
        download()
