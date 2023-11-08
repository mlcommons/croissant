"""records_test module."""

import pandas as pd

from mlcroissant._src.tests.records import record_to_python


def test_record_to_python():
    assert record_to_python({
        "key1": 1,
        "key2": {
            "key3": pd.Timestamp("2017-01-01T12"),
            "key4": {"key5": b"foo", "key6": float("nan")},
        },
    }) == {
        "key1": 1,
        "key2": {"key3": "2017-01-01 12:00:00", "key4": {"key5": "foo", "key6": None}},
    }
    assert record_to_python({
        "image": (
            "<PIL.PngImagePlugin.PngImageFile image mode=L size=28x28 at"
            " 0x7F40B2EB5420>"
        )
    }) == {
        "image": (
            "<PIL.PngImagePlugin.PngImageFile image mode=L size=28x28 at"
            " <MEMORY_ADDRESS>>"
        )
    }
