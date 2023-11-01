"""Test utils to handle records."""

import math
import re
from typing import Any

import pandas as pd


def record_to_python(record: Any):
    """Converts a record to a fully Python-native object.

    Warning: this function must be used for testing-purposes only!

    Records may contain non-serializable values (like `nan` or `pd.Timestamp` for
    example). This util converts records to Python-native objects:
    - bytes -> str
    - nan -> None
    - pd.Timestamp -> pd.Timestamp.strftime
    """
    if isinstance(record, bytes):
        return record.decode()
    elif isinstance(record, pd.Timestamp):
        return record.strftime("%Y-%m-%d %X")
    elif isinstance(record, float) and math.isnan(record):
        return None
    elif isinstance(record, (bool, float, int)):
        return record
    elif not isinstance(record, dict):
        str_repr = str(record)
        # Remove memory addresses from string representation.
        memory_addresses = re.compile(r"0x[0-9a-fA-F]+")
        return memory_addresses.sub("<MEMORY_ADDRESS>", str_repr)
    else:
        # Record is a dict
        for key, value in record.items():
            record[key] = record_to_python(value)
        return record
