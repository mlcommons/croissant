"""records_test module."""

import pandas as pd

from ml_croissant._src.tests.records import record_to_python


def test_record_to_python():
    assert record_to_python(
        {
            "key1": 1,
            "key2": {
                "key3": pd.Timestamp("2017-01-01T12"),
                "key4": {"key5": b"foo", "key6": float("nan")},
            },
        }
    ) == {
        "key1": 1,
        "key2": {"key3": "2017-01-01 12:00:00", "key4": {"key5": "Zm9v", "key6": None}},
    }
