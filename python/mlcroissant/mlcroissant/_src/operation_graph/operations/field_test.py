"""field_test module."""

from unittest import mock

import numpy as np
import pandas as pd
from PIL import Image
import pytest

from mlcroissant._src.core import constants
from mlcroissant._src.operation_graph.operations import field
from mlcroissant._src.tests.nodes import empty_field
from mlcroissant._src.tests.operations import operations


def test_str_representation():
    operation = field.ReadField(operations=operations(), node=empty_field)
    assert str(operation) == "ReadField(field_name)"


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
    expected = field._cast_value(
        b"PNG...Some image...", constants.SCHEMA_ORG_DATA_TYPE_IMAGE_OBJECT
    )
    open_mock.assert_called_once()
    assert expected == "opened_image"
