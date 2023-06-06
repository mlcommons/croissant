"""data_types module."""

from format.src import constants
import pandas as pd

EXPECTED_DATA_TYPES: dict[str, str] = {
    constants.SCHEMA_ORG_DATA_TYPE_BOOL: bool,
    constants.SCHEMA_ORG_DATA_TYPE_DATE: pd.DatetimeTZDtype,
    constants.SCHEMA_ORG_DATA_TYPE_FLOAT: float,
    constants.SCHEMA_ORG_DATA_TYPE_INTEGER: int,
    constants.SCHEMA_ORG_DATA_TYPE_TEXT: str,
    constants.SCHEMA_ORG_DATA_TYPE_URL: str,
    constants.SCHEMA_ORG_EMAIL: str,
    constants.SCHEMA_ORG_URL: str,
}
