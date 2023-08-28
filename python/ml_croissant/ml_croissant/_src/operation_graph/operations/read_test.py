"""read_test module."""

import pathlib
import tempfile
from unittest import mock

from etils import epath
import pandas as pd
import pytest

from ml_croissant._src.core.path import Path
from ml_croissant._src.operation_graph.operations.read import Read
from ml_croissant._src.tests.nodes import create_test_file_object
from ml_croissant._src.tests.nodes import empty_file_object


def test_str_representation():
    operation = Read(
        node=empty_file_object,
        folder=epath.Path(),
        url="http://mlcommons.org",
        fields=[],
    )
    assert str(operation) == "Read(file_object_name)"


def test_explicit_message_when_pyarrow_is_not_installed():
    with mock.patch.object(pd, "read_parquet", side_effect=ImportError):
        with tempfile.TemporaryDirectory() as folder:
            url = "file.parquet"
            folder = epath.Path(folder)
            # Create filepath = `folder/file.parquet`.
            filepath = folder / url
            file = Path(filepath=filepath, fullpath=pathlib.PurePath())
            filepath.touch()
            read = Read(
                node=create_test_file_object(encoding_format="application/x-parquet"),
                folder=folder,
                url=url,
                fields=[],
            )
            with pytest.raises(
                ImportError, match=".*pip install ml_croissant\\[parquet\\].*"
            ):
                read([file])
