"""extract_test module."""

import pathlib
import tarfile

from etils import epath
import pytest

from mlcroissant._src.core.path import get_fullpaths
from mlcroissant._src.operation_graph.operations.extract import _extract_file
from mlcroissant._src.operation_graph.operations.extract import Extract
from mlcroissant._src.tests.nodes import empty_file_object
from mlcroissant._src.tests.operations import operations


def test_str_representation():
    operation = Extract(operations=operations(), node=empty_file_object)
    assert str(operation) == "Extract(file_object_name)"


def test_get_fullpaths():
    files = [
        epath.Path("/path/to/extract/file1"),
        epath.Path("/path/to/extract/file2/foo"),
        epath.Path("/path/to/extract/file2/bar"),
    ]
    extract_dir = epath.Path("/path/to/extract")
    assert get_fullpaths(files, extract_dir) == [
        pathlib.PurePath("file1"),
        pathlib.PurePath("file2/foo"),
        pathlib.PurePath("file2/bar"),
    ]


def test_extract_tar_file_safe(tmp_path: pathlib.Path):
    archive = tmp_path / "archive.tar"
    payload = tmp_path / "data.txt"
    payload.write_text("hello")
    with tarfile.open(archive, "w") as tar:
        tar.add(payload, arcname="subdir/data.txt")

    target = tmp_path / "extracted"
    _extract_file(epath.Path(archive), epath.Path(target))

    assert (target / "subdir" / "data.txt").read_text() == "hello"


def test_extract_tar_file_rejects_path_traversal(tmp_path: pathlib.Path):
    archive = tmp_path / "traversal.tar"
    payload = tmp_path / "payload.txt"
    payload.write_text("evil")
    with tarfile.open(archive, "w") as tar:
        tar.add(payload, arcname="../evil.txt")

    target = tmp_path / "extracted"
    target.mkdir()
    tar_error = getattr(tarfile, "FilterError", ValueError)
    with pytest.raises((tar_error, ValueError)):
        _extract_file(epath.Path(archive), epath.Path(target))

    assert not (tmp_path / "evil.txt").exists()


def test_extract_tar_file_rejects_traversal_without_data_filter(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delattr(tarfile, "data_filter", raising=False)
    archive = tmp_path / "traversal.tar"
    payload = tmp_path / "payload.txt"
    payload.write_text("evil")
    with tarfile.open(archive, "w") as tar:
        tar.add(payload, arcname="../evil.txt")

    target = tmp_path / "extracted"
    target.mkdir()
    with pytest.raises(ValueError, match="Attempted path traversal"):
        _extract_file(epath.Path(archive), epath.Path(target))

    assert not (tmp_path / "evil.txt").exists()
