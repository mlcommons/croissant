"""bounding_box_test module."""

import pytest

from mlcroissant._src.core.ml import bounding_box


def test_parse():
    assert bounding_box.parse([1, 2, 3, 4]) == [1.0, 2.0, 3.0, 4.0]
    assert bounding_box.parse("1 2 3 4") == [1.0, 2.0, 3.0, 4.0]
    assert bounding_box.parse("1.0 2 3.0 4.0") == [1.0, 2.0, 3.0, 4.0]
    with pytest.raises(ValueError, match="Wrong format"):
        bounding_box.parse(42)
    with pytest.raises(ValueError, match="should have a length of"):
        bounding_box.parse([1, 2, 3, 4, 5])
    with pytest.raises(ValueError, match="can be converted to floats"):
        bounding_box.parse(["one", "two", "three", "four"])
