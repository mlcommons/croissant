"""Parse JSON operation."""

import jsonpath_rw
import pandas as pd

from mlcroissant._src.core.types import Json
from mlcroissant._src.structure_graph.nodes.field import Field


def parse_json_content(json: Json, fields: tuple[Field, ...]) -> pd.DataFrame:
    """Parsed all JSONs defined in the fields of RecordSet and outputs a pd.DF."""
    series = {}
    for field in fields:
        json_path = field.source.extract.json_path
        if json_path is None:
            continue
        jsonpath_expression = jsonpath_rw.parse(json_path)
        values = [match.value for match in jsonpath_expression.find(json)]
        series[json_path] = values
    return pd.DataFrame(series)
