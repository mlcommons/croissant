"""Test utils to handle records."""

import base64
import math
from typing import Any

import pandas as pd


def record_to_python(record: Any):
    """Converts a record to a fully Python-native object.

    Records may contain non-serializable values (like `nan` or `pd.Timestamp` for
    example). This util converts records to Python-native objects:
    - bytes -> str
    - nan -> None
    - pd.Timestamp -> pd.Timestamp.strftime
    """
    if isinstance(record, bytes):
        encoded = base64.b64encode(record)
        return encoded.decode()
    if isinstance(record, pd.Timestamp):
        return record.strftime("%Y-%m-%d %X")
    elif isinstance(record, float) and math.isnan(record):
        return None
    elif not isinstance(record, dict):
        return record
    else:
        # Record is a dict
        for key, value in record.items():
            record[key] = record_to_python(value)
        return record
