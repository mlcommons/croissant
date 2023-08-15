"""Parse JSON operation."""

from typing import Any

import jsonpath_rw
from ml_croissant._src.structure_graph.nodes import Field, RecordSet
import networkx as nx
import pandas as pd

import pandas as pd

from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.structure_graph.nodes import Field
from ml_croissant._src.structure_graph.nodes import RecordSet

Json = dict[str, Any]


def get_fields(record_set: RecordSet, graph: nx.MultiDiGraph) -> list[Field]:
    """Gets the fields of a given record set.

    TODO(https://github.com/mlcommons/croissant/issues/164): In the future, this will
    be added to RecordSet's API: `record_set.fields`.
    """
    fields: list[Field] = []
    for node in graph.nodes:
        if isinstance(node, Field) and node.parent == record_set:
            fields.append(node)
    return fields


def parse_json_content(json: Json, fields: list[Field]) -> pd.DataFrame:
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
