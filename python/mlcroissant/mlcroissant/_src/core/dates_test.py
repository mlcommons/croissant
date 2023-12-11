"""Tests for dates."""

import datetime

import pytest

from mlcroissant._src.core.dates import from_str_to_date_time
from mlcroissant._src.core.issues import Issues


@pytest.mark.parametrize(
    ["date", "expected", "errors"],
    [
        ["20240101", datetime.datetime(year=2024, month=1, day=1), set()],
        ["2024-01-01", datetime.datetime(year=2024, month=1, day=1), set()],
        [20240101, None, set(["Wrong type for date. Expected str. Got <class 'int'>"])],
        [
            "foo",
            None,
            set([
                "Dates or DateTimes should follow the [ISO 8601"
                " format](https://en.wikipedia.org/wiki/ISO_8601). Got foo"
            ]),
        ],
    ],
)
def test_from_str_to_date_time(
    date: str, expected: datetime.datetime, errors: set[str]
):
    issues = Issues()
    result = from_str_to_date_time(issues, date)
    assert issues.errors == errors
    assert expected == result
