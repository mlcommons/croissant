"""Utils to manipulate dates/date times."""

import datetime
from typing import Any

import dateutil.parser

from mlcroissant._src.core.issues import Issues


def from_str_to_datetime(issues: Issues, date: str | None) -> datetime.datetime | None:
    """Converts https://schema.org/DateTime or https://schema.org/Date to datetime."""
    if date is None:
        return None
    elif isinstance(date, str):
        # https://schema.org/Date follows the ISO 8601 date format.
        # https://schema.org/DateTime has the form [-]CCYY-MM-DDThh:mm:ss[Z|(+|-)hh:mm]
        # in the ISO 8601 format.
        try:
            return dateutil.parser.isoparse(date)
        except ValueError:
            issues.add_error(
                "Dates or DateTimes should follow the [ISO 8601"
                f" format](https://en.wikipedia.org/wiki/ISO_8601). Got {date}"
            )
    else:
        issues.add_error(f"Wrong type for date. Expected str. Got {type(date)}")
    return None


def from_datetime_to_str(date: datetime.datetime | None) -> str | None:
    """Converts a datetime to https://schema.org/Date (ISO 8601 date format)."""
    if date is None:
        return None
    elif date.time() == datetime.time.min:
        return date.strftime("%Y-%m-%d")
    return date.isoformat()


def cast_date(date: Any) -> datetime.datetime | None:
    """Casts date as a datetime for any input."""
    if date is None or isinstance(date, datetime.datetime):
        return date
    elif isinstance(date, str):
        issues = Issues()
        date = from_str_to_datetime(issues, date)
        if issues.errors:
            raise ValueError(issues.errors)
        return date
    elif isinstance(date, datetime.date):
        return datetime.datetime.combine(date, datetime.time.min)
    raise ValueError(f"Wrong type for a date. Expected Date or Datetime. Got: {date}")


def cast_dates(value: Any) -> list[datetime.datetime] | None:
    """Casts dates as datetimes for any input."""
    if isinstance(value, list):
        dates = []
        for v in value:
            date = cast_date(v)
            if date is None:
                return None
            else:
                dates.append(date)
        return dates
    return cast_dates([value])
