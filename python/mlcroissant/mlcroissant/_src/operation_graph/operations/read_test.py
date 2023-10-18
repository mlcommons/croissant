"""read_test module."""

import pathlib
import tempfile
from unittest import mock

from etils import epath
import pandas as pd
import pytest

from mlcroissant._src.core.path import Path
from mlcroissant._src.operation_graph.operations.read import Read
from mlcroissant._src.tests.nodes import create_test_file_object
from mlcroissant._src.tests.nodes import empty_file_object
from mlcroissant._src.tests.operations import operations


def test_str_representation():
    operation = Read(
        operations=operations(),
        node=empty_file_object,
        folder=epath.Path(),
        fields=[],
    )
    assert str(operation) == "Read(file_object_name)"


def test_explicit_message_when_pyarrow_is_not_installed():
    with mock.patch.object(pd, "read_parquet", side_effect=ImportError):
        with tempfile.TemporaryDirectory() as folder:
            content_url = "file.parquet"
            folder = epath.Path(folder)
            # Create filepath = `folder/file.parquet`.
            filepath = folder / content_url
            file = Path(filepath=filepath, fullpath=pathlib.PurePath())
            filepath.touch()
            read = Read(
                operations=operations(),
                node=create_test_file_object(
                    encoding_format="application/x-parquet", content_url=content_url
                ),
                folder=folder,
                fields=[],
            )
            with pytest.raises(
                ImportError, match=".*pip install mlcroissant\\[parquet\\].*"
            ):
                read([file])
