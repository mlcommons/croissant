"""concatenate_test module."""

import pathlib

from etils import epath
import pytest

from mlcroissant._src.core.path import Path
from mlcroissant._src.operation_graph.operations import concatenate
from mlcroissant._src.structure_graph.nodes.source import FileProperty
from mlcroissant._src.tests.nodes import empty_file_set
from mlcroissant._src.tests.operations import operations


def test_str_representation():
    operation = concatenate.Concatenate(operations=operations(), node=empty_file_set)
    assert str(operation) == "Concatenate(file_set_name)"


def _path(fullpath: str) -> Path:
    return Path(
        filepath=epath.Path("/extracted") / fullpath,
        fullpath=pathlib.PurePath(fullpath),
    )


@pytest.mark.parametrize(
    "args",
    [
        # Sequential execution passes the whole list of files.
        ([_path("train/cat1.jpg"), _path("test/cat3.jpg")],),
        # Beam execution passes one file per element.
        (_path("train/cat1.jpg"), _path("test/cat3.jpg")),
        ([_path("train/cat1.jpg")], _path("test/cat3.jpg")),
    ],
)
def test_call_accepts_paths_and_lists_of_paths(args):
    operation = concatenate.Concatenate(operations=operations(), node=empty_file_set)
    df = operation.call(*args)
    assert df[FileProperty.fullpath].tolist() == ["train/cat1.jpg", "test/cat3.jpg"]
    assert df[FileProperty.filename].tolist() == ["cat1.jpg", "cat3.jpg"]
    assert df[FileProperty.filepath].tolist() == [
        "/extracted/train/cat1.jpg",
        "/extracted/test/cat3.jpg",
    ]
