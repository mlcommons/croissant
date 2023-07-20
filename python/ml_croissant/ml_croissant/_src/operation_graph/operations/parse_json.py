"""Parse JSON operation."""

from typing import Any

import jsonpath_rw
from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.structure_graph.nodes import Field, RecordSet
import pandas as pd


class ParseJson(Operation):
    """Parsed all JSONs defined in the fields of RecordSet and outputs a pd.DF."""

    node: RecordSet

    def __call__(self, json: dict[str, Any], fields: list[Field] | None = None):
        """See class' docstring."""
        series = {}
        for field in fields:
            json_path = field.source.extract.json_path
            if json_path is None:
                continue
            jsonpath_expression = jsonpath_rw.parse(json_path)
            values = [match.value for match in jsonpath_expression.find(json)]
            series[json_path] = values
        return pd.DataFrame(series)
