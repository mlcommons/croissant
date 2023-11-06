"""field_test module."""

import tempfile
from unittest import mock

import numpy as np
import pandas as pd
from PIL import Image
import pytest

from mlcroissant._src.core.constants import DataType
from mlcroissant._src.operation_graph.operations import field
from mlcroissant._src.structure_graph.nodes.source import FileProperty
from mlcroissant._src.tests.nodes import empty_record_set
from mlcroissant._src.tests.operations import operations


def test_str_representation():
    operation = field.ReadField(operations=operations(), node=empty_record_set)
    assert str(operation) == "ReadField(record_set_name)"


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
        row = pd.Series({FileProperty.filepath: path})
        series = field._extract_lines(row)
        expected = pd.Series(
            {
                FileProperty.filepath: path,
                FileProperty.lines: [b"bon jour  ", b"", b" h\xc3\xa9llo ", b"hallo "],
                FileProperty.lineNumbers: [0, 1, 2, 3],
            }
        )
        pd.testing.assert_series_equal(series, expected)


# TODO: Add a test here.
