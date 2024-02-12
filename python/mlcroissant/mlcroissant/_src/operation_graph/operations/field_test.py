"""field_test module."""

import tempfile
from unittest import mock

import numpy as np
import pandas as pd
from PIL import Image
import pytest

from mlcroissant._src.core.constants import DataType
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
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
from mlcroissant._src.tests.versions import parametrize_conforms_to


def test_str_representation():
    operation = field.ReadFields(operations=operations(), node=empty_record_set)
    assert str(operation) == "ReadFields(record_set_name)"


@parametrize_conforms_to()
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
def test_cast_value(conforms_to, value, data_type, expected):
    ctx = Context(conforms_to=conforms_to)
    assert field._cast_value(ctx, value, data_type) == expected


@parametrize_conforms_to()
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
def test_cast_value_nan(conforms_to, value, data_type):
    ctx = Context(conforms_to=conforms_to)
    assert np.isnan(field._cast_value(ctx, value, data_type))


@parametrize_conforms_to()
@mock.patch.object(Image, "open", return_value="opened_image")
def test_cast_value_image(open_mock, conforms_to):
    ctx = Context(conforms_to=conforms_to)
    expected = field._cast_value(ctx, b"PNG...Some image...", DataType.IMAGE_OBJECT)
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
        ctx = Context(conforms_to=CroissantVersion.V_1_0)
        Metadata(
            ctx=ctx,
            name="metadata",
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


@pytest.mark.parametrize(
    ["value", "source", "data_type", "expected_value"],
    [
        # Capturing group
        [
            "train1234",
            Source(transforms=[Transform(regex="(train|val)\\d\\d\\d\\d")]),
            DataType.TEXT,
            "train",
        ],
        # Non working capturing group
        [
            "foo1234",
            Source(transforms=[Transform(regex="(train|val)\\d\\d\\d\\d")]),
            DataType.TEXT,
            "foo1234",
        ],
        [
            {"one": {"two": "expected_value"}, "three": "non_expected_value"},
            Source(transforms=[Transform(json_path="one.two")]),
            DataType.TEXT,
            "expected_value",
        ],
        [
            pd.Timestamp("2024-12-10 12:00:00"),
            Source(transforms=[Transform(format="%Y-%m-%d")]),
            DataType.DATE,
            "2024-12-10",
        ],
        [
            "2024-12-10 12:00:00",
            Source(transforms=[Transform(format="%Y-%m-%d")]),
            DataType.DATE,
            "2024-12-10",
        ],
    ],
)
def test_apply_transforms_fn(value, source, data_type, expected_value):
    f = Field(name="test", data_types=data_type, source=source)
    assert field.apply_transforms_fn(value, f) == expected_value
