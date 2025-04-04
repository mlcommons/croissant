"""data_types module."""

import numpy as np
import pandas as pd
from rdflib import term

from mlcroissant._src.core import constants
from mlcroissant._src.core.constants import DataType
from mlcroissant._src.core.context import Context
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


EXPECTED_DATA_TYPES: dict[term.URIRef, type] = {
    DataType.BOOL: bool,
    DataType.DATE: pd.Timestamp,
    DataType.FLOAT: float,
    DataType.FLOAT16: np.float16,
    DataType.FLOAT32: np.float32,
    DataType.FLOAT64: np.float64,
    DataType.INTEGER: int,
    DataType.INT8: np.int8,
    DataType.INT16: np.int16,
    DataType.INT32: np.int32,
    DataType.INT64: np.int64,
    DataType.TEXT: bytes,
    DataType.URL: bytes,
    DataType.UINT8: np.uint8,
    DataType.UINT16: np.uint16,
    DataType.UINT32: np.uint32,
    DataType.UINT64: np.uint64,
}


def data_types_from_jsonld(ctx: Context, data_types: Json):
    """Extracts DataType from its JSON-LD."""
    if isinstance(data_types, dict):
        data_type = data_types.get("@id")
        if isinstance(data_type, str):
            data_type = term.URIRef(data_type)
        return data_type
    elif isinstance(data_types, (str, term.URIRef)):
        return term.URIRef(data_types)
    elif isinstance(data_types, list):
        return [data_types_from_jsonld(ctx, d) for d in data_types]
    return []


def data_types_to_jsonld(ctx: Context, data_types: list[term.URIRef] | None):
    """Converts DataType to JSON-LD."""
    if data_types:
        return [ctx.rdf.shorten_value(data_type) for data_type in data_types]
    return None
