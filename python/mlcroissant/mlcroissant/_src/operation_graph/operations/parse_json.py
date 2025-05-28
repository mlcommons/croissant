"""Parse JSON operation."""

import json
import jmespath
import jsonpath_rw
import orjson
import pandas as pd
from typing import TextIO

from mlcroissant._src.core.types import Any
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.source import FileProperty


def parse_json_content(json_obj, fields):
    """Parsed all JSONs defined in the fields of RecordSet and outputs a pd.DF."""
    series = {}
    for field in fields:
        jp = field.source.extract.json_path
        if not jp:
            continue
        expr = jsonpath_rw.parse(jp)
        vals = []
        for match in expr.find(json_obj):
            v = match.value
            # if we got back a one‐item list, unwrap it
            if isinstance(v, list) and len(v) == 1:
                v = v[0]
            vals.append(v)
        series[jp] = vals
    return pd.DataFrame(series)


class JsonReader:
    def __init__(self, fields: tuple[Field, ...]):
        # build a list of (original_jsonpath, engine, compiled_expr)
        self.exprs: list[tuple[str, str, Any]] = []
        for field in fields:
            jp = field.source.extract.json_path
            if not jp:
                continue

            # decide whether this path can be JMESPath or needs full JSONPath
            stripped = jp.lstrip("$.")
            if ".." in jp:
                # uses recursive‐descent → fall back to jsonpath_ng
                expr = jsonpath_rw.parse(jp)
                engine = "jsonpath"
            else:
                # simple direct path → use JMESPath
                expr = jmespath.compile(stripped)
                engine = "jmespath"

            self.exprs.append((jp, engine, expr))
        self.fields = fields

    def parse(self, fh: TextIO) -> pd.DataFrame:
        # Load entire JSON file (could be a list or a single dict)
        raw = fh.read()
        data = orjson.loads(raw)

        # Always treat as list of records
        records = data if isinstance(data, list) else [data]

        series: dict[str, list] = {}
        for jp, engine, expr in self.exprs:
            vals: list = []
            for rec in records:
                if engine == "jmespath":
                    out = expr.search(rec)
                    # unwrap single‐item lists
                    if isinstance(out, list):
                        if len(out) == 1:
                            out = out[0]
                        elif len(out) == 0:
                            out = None
                else:  # jsonpath_ng
                    matches = expr.find(rec)
                    out = [m.value for m in matches]
                    if len(out) == 1:
                        out = out[0]
                    elif not out:
                        out = None

                # flatten: if out is a list, extend; else append scalar (unless None)
                if isinstance(out, list):
                    vals.extend(out)
                elif out is not None:
                    vals.append(out)

            series[jp] = vals

        return pd.DataFrame(series)

    def raw(self, fh: TextIO) -> pd.DataFrame:
        # raw JSON fallback: one‐cell DataFrame
        fh.seek(0)
        content = json.load(fh)
        return pd.DataFrame({ FileProperty.content: [content] })



class JsonlReader:
    def __init__(self, fields):
        self.exprs = []  # list of (orig_path, engine, compiled_expr)
        for field in fields:
            jp = field.source.extract.json_path
            if not jp:
                continue

            if jp.startswith("$.") and ".." not in jp:
                # simple JSONPath → JMESPath
                jm = jp.lstrip("$.")      # drop the "$."
                expr = jmespath.compile(jm)
                engine = "jmespath"
            else:
                # anything with recursive‐descent or complex filters
                expr = jsonpath_rw.parse(jp)
                engine = "jsonpath"
            
            self.exprs.append((jp, engine, expr))
        self.fields = fields

    def parse(self, fh):
        rows = []
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = orjson.loads(line)
            row = {}
            for jp, engine, expr in self.exprs:
                if engine == "jmespath":
                    val = expr.search(rec)
                    # unwrap single‐item lists if you like:
                    if isinstance(val, list):
                        val = val[0] if len(val)==1 else val
                else:
                    matches = expr.find(rec)
                    # jsonpath_ng gives you a list of Match objects
                    val = [m.value for m in matches]
                    if len(val) == 1:
                        val = val[0]
                row[jp] = val
            rows.append(row)
        return pd.DataFrame(rows)

    def raw(self, fh: TextIO) -> pd.DataFrame:
        fh.seek(0)
        return pd.read_json(fh, lines=True)