"""Tests for dates."""

import datetime

import pytest

from mlcroissant._src.core.dates import from_datetime_to_str
from mlcroissant._src.core.dates import from_str_to_datetime
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
def test_from_str_to_datetime(date: str, expected: datetime.datetime, errors: set[str]):
    issues = Issues()
    result = from_str_to_datetime(issues, date)
    assert issues.errors == errors
    assert expected == result


@pytest.mark.parametrize(
    ["date", "expected"],
    [
        [None, None],
        [datetime.datetime(year=2024, month=1, day=1), "2024-01-01"],
        [
            datetime.datetime(year=2024, month=1, day=1, hour=12, minute=20),
            "2024-01-01T12:20:00",
        ],
    ],
)
def test_from_datetime_to_str(date: datetime.datetime | None, expected: str):
    assert from_datetime_to_str(date) == expected
