"""Tests for data_types."""

import numpy as np
import pytest

from .data_types import convert_dtype


def test_convert_dtype():
    convert_dtype(np.int64) == "https://schema.org/Integer"
    convert_dtype(np.float64) == "https://schema.org/Float"
    convert_dtype(np.bool_) == "https://schema.org/Boolean"
    convert_dtype(np.str_) == "https://schema.org/Text"
    with pytest.raises(NotImplementedError):
        convert_dtype(np.float32)
