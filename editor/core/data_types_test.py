"""Tests for data_types."""

import numpy as np
import pytest

import mlcroissant as mlc

from .data_types import convert_dtype
from .data_types import str_to_mlc_data_type


def test_convert_dtype():
    convert_dtype(np.int64) == "https://schema.org/Integer"
    convert_dtype(np.float64) == "https://schema.org/Float"
    convert_dtype(np.bool_) == "https://schema.org/Boolean"
    convert_dtype(np.str_) == "https://schema.org/Text"
    with pytest.raises(NotImplementedError):
        convert_dtype(np.float32)


def test_str_to_mlc_data_type():
    assert str_to_mlc_data_type("Integer") == mlc.DataType.INTEGER
    assert str_to_mlc_data_type("Foo") == None
