"""Utils to manipulate dates/date times."""

import datetime

import dateutil.parser

from mlcroissant._src.core.issues import Issues


def from_str_to_date_time(issues: Issues, date: str | None) -> datetime.datetime | None:
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
