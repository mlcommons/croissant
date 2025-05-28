"""Parse JSON operation."""

import jsonpath_rw
import pandas as pd

from mlcroissant._src.core.types import Json
from mlcroissant._src.structure_graph.nodes.field import Field


def parse_json_content(json: Json, fields: tuple[Field, ...]) -> pd.DataFrame:
    """Parsed all JSONs defined in the fields of RecordSet and outputs a pd.DF."""
    lines = json if isinstance(json, list) else [json]
    rows = []
    for line in lines:
        row = {}
        for field in fields:
            path = field.source.extract.json_path
            if not path:
                continue
            expr = jsonpath_rw.parse(path)
            matches = expr.find(line)
            if matches:
                # if you expect a single value, grab the first
                row[path] = matches[0].value
        rows.append(row)
    return pd.DataFrame(rows)
