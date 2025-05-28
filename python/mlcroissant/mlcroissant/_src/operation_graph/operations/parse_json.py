"""Parse JSON operation."""

import json
from typing import Iterator, TextIO
import jsonpath_rw
import orjson, jmespath
import pandas as pd

from mlcroissant._src.core.types import Json
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.source import FileProperty


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


class JsonReader:
    def __init__(self, fields: tuple[Field, ...]):
        # pre‐compile JSONPath / JMESPath here if you like
        self.exprs = {
            fd.source.extract.json_path: jmespath.compile(fd.source.extract.json_path)
            for fd in fields
            if fd.source.extract.json_path
        }
        self.fields = fields

    def parse(self, fh: TextIO) -> pd.DataFrame:
        content = json.load(fh)
        return parse_json_content(content, self.fields)

    def raw(self, fh: TextIO) -> pd.DataFrame:
        content = json.load(fh)
        return pd.DataFrame({ FileProperty.content: [content] })


class JsonlReader:
    def __init__(self, fields: tuple[Field, ...]):
        # pre‐compile JSONPath / JMESPath here if you like
        self.exprs: dict[str, jmespath.Compiled] = {}
        for field in fields:
            jp = field.source.extract.json_path
            if not jp:
                continue
            # strip leading '$.' only for compilation
            jm = jp.lstrip("$.")
            self.exprs[jp] = jmespath.compile(jm) 
        self.fields = fields

    def parse(self, fh: TextIO) -> pd.DataFrame:
        rows = []
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = orjson.loads(line)
            row: dict[str, object] = {}
            for original_path, expr in self.exprs.items():
                # use the original_path as the column name
                row[original_path] = expr.search(rec)
            rows.append(row)
        return pd.DataFrame(rows)

    def raw(self, fh: TextIO) -> pd.DataFrame:
        fh.seek(0)
        return pd.read_json(fh, lines=True)
