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
        [
            datetime.datetime(
                year=2024,
                month=1,
                day=1,
                hour=12,
                minute=0,
                tzinfo=datetime.timezone.utc,
            ),
            "2024-01-01T12:00:00Z",
        ],
        [
            datetime.datetime(
                year=2024,
                month=1,
                day=1,
                hour=12,
                minute=0,
                tzinfo=datetime.timezone(datetime.timedelta(hours=1)),
            ),
            "2024-01-01T12:00:00+01:00",
        ],
    ],
)
def test_from_datetime_to_str(date: datetime.datetime | None, expected: str):
    assert from_datetime_to_str(date) == expected


@pytest.mark.parametrize("offset_hours", [0, 9, -5.5, -12, 14])
def test_midnight_with_timezone_round_trips(offset_hours: float):
    date = datetime.datetime(
        2024,
        3,
        18,
        tzinfo=datetime.timezone(datetime.timedelta(hours=offset_hours)),
    )
    serialized = from_datetime_to_str(date)
    issues = Issues()
    restored = from_str_to_datetime(issues, serialized)
    assert not issues.errors
    assert restored is not None
    assert restored == date
    assert restored.utcoffset() == date.utcoffset()


@pytest.mark.parametrize("microsecond", [0, 1])
def test_midnight_utc_serialization(microsecond: int):
    date = datetime.datetime(
        2024, 3, 18, microsecond=microsecond, tzinfo=datetime.timezone.utc
    )
    expected = "2024-03-18T00:00:00" + (".000001" if microsecond else "") + "Z"
    assert from_datetime_to_str(date) == expected
