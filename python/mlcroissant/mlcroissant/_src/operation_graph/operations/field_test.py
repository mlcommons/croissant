"""field_test module."""

import tempfile
from unittest import mock

import numpy as np
import pandas as pd
from PIL import Image
import pytest

from mlcroissant._src.core.constants import DataType
from mlcroissant._src.operation_graph.base_operation import Operations
from mlcroissant._src.operation_graph.operations import field
from mlcroissant._src.operation_graph.operations import ReadFields
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.file_object import FileObject
from mlcroissant._src.structure_graph.nodes.metadata import Metadata
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet
from mlcroissant._src.structure_graph.nodes.source import Extract
from mlcroissant._src.structure_graph.nodes.source import FileProperty
from mlcroissant._src.structure_graph.nodes.source import Source
from mlcroissant._src.structure_graph.nodes.source import Transform
from mlcroissant._src.tests.nodes import empty_record_set
from mlcroissant._src.tests.operations import operations


def test_str_representation():
    operation = field.ReadFields(operations=operations(), node=empty_record_set)
    assert str(operation) == "ReadFields(record_set_name)"


@pytest.mark.parametrize(
    ["value", "data_type", "expected"],
    [
        [b"iambytes", bytes, b"iambytes"],
        ["iamstring", bytes, b"iamstring"],
        [8, bytes, b"8"],
        [1, float, 1.0],
        ["1", float, 1.0],
        [1.0, float, 1.0],
        ["2024-12-10", pd.Timestamp, pd.Timestamp("2024-12-10")],
    ],
)
def test_cast_value(value, data_type, expected):
    assert field._cast_value(value, data_type) == expected


@pytest.mark.parametrize(
    ["value", "data_type"],
    [
        [np.nan, bool],
        [np.nan, bytes],
        [np.nan, pd.Timestamp],
        [np.nan, float],
        [np.nan, int],
    ],
)
def test_cast_value_nan(value, data_type):
    assert np.isnan(field._cast_value(value, data_type))


@mock.patch.object(Image, "open", return_value="opened_image")
def test_cast_value_image(open_mock):
    expected = field._cast_value(b"PNG...Some image...", DataType.IMAGE_OBJECT)
    open_mock.assert_called_once()
    assert expected == "opened_image"


@pytest.mark.parametrize(
    "separator",
    [
        b"\n",
        b"\r",
        b"\r\n",
    ],
)
def test_extract_lines(separator):
    with tempfile.TemporaryDirectory() as tempdir:
        # Create the underlying file.
        content = (
            b"bon jour  "
            + separator
            + separator
            + b" h\xc3\xa9llo "
            + separator
            + b"hallo "
            + separator
        )
        path = tempdir + "/file.txt"
        with open(path, "wb") as f:
            f.write(content)

        # Create all needed nodes.
        distribution = [
            FileObject(
                name="file",
                content_url=path,
                sha256="None",
                encoding_format="text/plain",
            )
        ]
        fields = []
        fields.append(
            Field(
                name="line",
                data_types=[DataType.TEXT],
                source=Source(
                    uid="file", extract=Extract(file_property=FileProperty.lines)
                ),
            )
        )
        fields.append(
            Field(
                name="line_number",
                data_types=[DataType.INTEGER],
                source=Source(
                    uid="file", extract=Extract(file_property=FileProperty.lineNumbers)
                ),
            )
        )
        fields.append(
            Field(
                name="filename",
                data_types=[DataType.TEXT],
                source=Source(
                    uid="file",
                    extract=Extract(file_property=FileProperty.filepath),
                    transforms=[Transform(regex=".*\\/(\\w*)\\.txt")],
                ),
            )
        )
        record_sets = [RecordSet(name="main", fields=fields)]
        Metadata(
            name="metadata",
            conforms_to="http://mlcommons.org/croissant/1.0",
            url="url.com",
            distribution=distribution,
            record_sets=record_sets,
        )
        read_field = ReadFields(operations=Operations(), node=record_sets[0])
        df = pd.DataFrame({FileProperty.filepath: [path]})
        expected = [
            {"line_number": 0, "line": b"bon jour  ", "filename": b"file"},
            {"line_number": 1, "line": b"", "filename": b"file"},
            {"line_number": 2, "line": b" h\xc3\xa9llo ", "filename": b"file"},
            {"line_number": 3, "line": b"hallo ", "filename": b"file"},
        ]
        result = list(read_field(df))
        assert result == expected
