"""data_types module."""

import pandas as pd

from ml_croissant._src.core import constants

EXPECTED_DATA_TYPES: dict[str, type] = {
    constants.SCHEMA_ORG_DATA_TYPE_BOOL: bool,
    constants.SCHEMA_ORG_DATA_TYPE_DATE: pd.Timestamp,
    constants.SCHEMA_ORG_DATA_TYPE_FLOAT: float,
    constants.SCHEMA_ORG_DATA_TYPE_INTEGER: int,
    constants.SCHEMA_ORG_DATA_TYPE_TEXT: str,
    constants.SCHEMA_ORG_DATA_TYPE_URL: str,
}
