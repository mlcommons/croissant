"""field_test module."""

import tempfile
from unittest import mock

from etils import epath
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


def test_readfield_with_subfields():
    with tempfile.TemporaryDirectory() as tempdir:
        csv_file = epath.Path(tempdir, "dummy_csv.csv")
        with csv_file.open("w") as f:
            f.write("latitude,longitude,names,surnames\n")
            f.write("1,1,Anna-Maria,Rossi-Bianchi\n")
            f.write("2,2,Giulia,Ferrari\n")
            f.write("1,3,,\n")
        # Nodes to define metadata.
        distribution = [
            FileObject(
                name="file",
                id="file_id",
                content_url=csv_file,
                sha256="None",
                encoding_format="text/csv",
            )
        ]
        fields = [
            # One field with subfields.
            Field(
                name="coordinates",
                id="main/coordinates",
                data_types=[DataType.TEXT],
                sub_fields=[
                    Field(
                        name="latitude",
                        id="main/coordinates/latitude",
                        data_types=[DataType.INTEGER],
                        source=Source(
                            file_object="file_id",
                            extract=Extract(column="latitude"),
                        ),
                    ),
                    Field(
                        name="longitude",
                        id="main/coordinates/longitude",
                        data_types=[DataType.INTEGER],
                        source=Source(
                            file_object="file_id",
                            extract=Extract(column="longitude"),
                        ),
                    ),
                ],
            ),
            # One field with repeated subfields.
            Field(
                name="checked_users",
                id="main/checked_users",
                data_types=[DataType.TEXT],
                repeated=True,
                sub_fields=[
                    Field(
                        name="name",
                        id="main/checked_users/name",
                        data_types=[DataType.TEXT],
                        source=Source(
                            file_object="file_id",
                            extract=Extract(column="names"),
                            transforms=[Transform(separator="-")],
                        ),
                    ),
                    Field(
                        name="surname",
                        id="main/checked_users/surname",
                        data_types=[DataType.TEXT],
                        source=Source(
                            file_object="file_id",
                            extract=Extract(column="surnames"),
                            transforms=[Transform(separator="-")],
                        ),
                    ),
                ],
            ),
        ]
        with mock.patch.object(RecordSet, "check_joins_in_fields") as mock_check_joins:
            mock_check_joins.return_value = True
            record_set = RecordSet(name="main", id="main", fields=fields)
            record_sets = [record_set]
            ctx = Context(conforms_to=CroissantVersion.V_1_0)
            Metadata(
                ctx=ctx,
                name="metadata",
                url="url.com",
                distribution=distribution,
                record_sets=record_sets,
            )
            read_field = ReadFields(operations=Operations(), node=record_sets[0])
            df = pd.read_csv(
                csv_file
            )  # pd.DataFrame({FileProperty.filepath: [csv_file]})
            expected = [
                {
                    "main/coordinates": {
                        "main/coordinates/latitude": 1,
                        "main/coordinates/longitude": 1,
                    },
                    "main/checked_users": [
                        {
                            "main/checked_users/name": b"Anna",
                            "main/checked_users/surname": b"Rossi",
                        },
                        {
                            "main/checked_users/name": b"Maria",
                            "main/checked_users/surname": b"Bianchi",
                        },
                    ],
                },
                {
                    "main/coordinates": {
                        "main/coordinates/latitude": 2,
                        "main/coordinates/longitude": 2,
                    },
                    "main/checked_users": [
                        {
                            "main/checked_users/name": b"Giulia",
                            "main/checked_users/surname": b"Ferrari",
                        },
                    ],
                },
                {
                    "main/coordinates": {
                        "main/coordinates/latitude": 1,
                        "main/coordinates/longitude": 3,
                    },
                    "main/checked_users": [
                        {
                            "main/checked_users/name": None,
                            "main/checked_users/surname": None,
                        },
                    ],
                },
            ]
            result = list(read_field.call(df))
            assert result == expected


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
                id="file_id",
                content_url=path,
                sha256="None",
                encoding_format="text/plain",
            )
        ]
        fields = []
        fields.append(
            Field(
                name="line",
                id="main/line",
                data_types=[DataType.TEXT],
                source=Source(
                    file_object="file_id",
                    extract=Extract(file_property=FileProperty.lines),
                ),
            )
        )
        fields.append(
            Field(
                name="line_number",
                id="main/line_number",
                data_types=[DataType.INTEGER],
                source=Source(
                    file_object="file_id",
                    extract=Extract(file_property=FileProperty.lineNumbers),
                ),
            )
        )
        fields.append(
            Field(
                name="filename",
                id="main/filename",
                data_types=[DataType.TEXT],
                source=Source(
                    file_object="file_id",
                    extract=Extract(file_property=FileProperty.filepath),
                    transforms=[Transform(regex=".*\\/(\\w*)\\.txt")],
                ),
            )
        )
        with mock.patch.object(RecordSet, "check_joins_in_fields") as mock_check_joins:
            mock_check_joins.return_value = True
            record_set = RecordSet(name="main", id="main", fields=fields)
            record_sets = [record_set]
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
                {
                    "main/line_number": 0,
                    "main/line": b"bon jour  ",
                    "main/filename": b"file",
                },
                {"main/line_number": 1, "main/line": b"", "main/filename": b"file"},
                {
                    "main/line_number": 2,
                    "main/line": b" h\xc3\xa9llo ",
                    "main/filename": b"file",
                },
                {
                    "main/line_number": 3,
                    "main/line": b"hallo ",
                    "main/filename": b"file",
                },
            ]
            result = list(read_field.call(df))
            assert result == expected


@pytest.mark.parametrize(
    ["value", "source", "data_type", "expected_value", "repeated"],
    [
        # Capturing group
        [
            "train1234",
            Source(transforms=[Transform(regex="(train|val)\\d\\d\\d\\d")]),
            DataType.TEXT,
            "train",
            False,
        ],
        [
            ["train1234", "train5678", "val1111"],
            Source(transforms=[Transform(regex="(train|val)\\d\\d\\d\\d")]),
            DataType.TEXT,
            ["train", "train", "val"],
            True,
        ],
        [
            epath.Path("path/to/train1234"),
            Source(transforms=[Transform(regex=".*/(train|val)\\d\\d\\d\\d")]),
            DataType.TEXT,
            "train",
            False,
        ],
        # Non working capturing group
        [
            "foo1234",
            Source(transforms=[Transform(regex="(train|val)\\d\\d\\d\\d")]),
            DataType.TEXT,
            "foo1234",
            False,
        ],
        [
            {"one": {"two": "expected_value"}, "three": "non_expected_value"},
            Source(transforms=[Transform(json_path="one.two")]),
            DataType.TEXT,
            "expected_value",
            False,
        ],
        [
            pd.Timestamp("2024-12-10 12:00:00"),
            Source(transforms=[Transform(format="%Y-%m-%d")]),
            DataType.DATE,
            "2024-12-10",
            False,
        ],
        [
            "2024-12-10 12:00:00",
            Source(transforms=[Transform(format="%Y-%m-%d")]),
            DataType.DATE,
            "2024-12-10",
            False,
        ],
    ],
)
def test_apply_transforms_fn(value, source, data_type, expected_value, repeated):
    f = Field(id="test", name="test", data_types=data_type, source=source)
    assert field.apply_transforms_fn(value, f, repeated=repeated) == expected_value
