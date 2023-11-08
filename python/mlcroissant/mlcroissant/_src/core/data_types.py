"""data_types module."""

import pandas as pd

from mlcroissant._src.core import constants
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.core.types import Json


def check_expected_type(issues: Issues, jsonld: Json, expected_type: str):
    """Checks that JSON-LD `jsonld` has "@type" == expected_type."""
    node_name = jsonld.get(constants.SCHEMA_ORG_NAME, "<unknown node>")
    node_type = jsonld.get("@type")
    if node_type != expected_type:
        issues.add_error(
            f'"{node_name}" should have an attribute "@type": "{expected_type}". Got'
            f" {node_type} instead."
        )


EXPECTED_DATA_TYPES: dict[str, type] = {
    constants.ML_COMMONS_DATA_TYPE_BOUNDING_BOX: (
        constants.ML_COMMONS_DATA_TYPE_BOUNDING_BOX
    ),
    constants.SCHEMA_ORG_DATA_TYPE_BOOL: bool,
    constants.SCHEMA_ORG_DATA_TYPE_DATE: pd.Timestamp,
    constants.SCHEMA_ORG_DATA_TYPE_FLOAT: float,
    constants.SCHEMA_ORG_DATA_TYPE_IMAGE_OBJECT: (
        constants.SCHEMA_ORG_DATA_TYPE_IMAGE_OBJECT
    ),
    constants.SCHEMA_ORG_DATA_TYPE_AUDIO_OBJECT: (
        constants.SCHEMA_ORG_DATA_TYPE_AUDIO_OBJECT
    ),
    constants.SCHEMA_ORG_DATA_TYPE_INTEGER: int,
    constants.SCHEMA_ORG_DATA_TYPE_TEXT: str,
    constants.SCHEMA_ORG_DATA_TYPE_URL: str,
}
