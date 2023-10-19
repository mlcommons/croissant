"""extract_test module."""

import pathlib

from etils import epath

from mlcroissant._src.core.path import get_fullpaths
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
