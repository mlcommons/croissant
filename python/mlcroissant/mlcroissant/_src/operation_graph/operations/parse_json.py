"""Parse JSON operation."""

from typing import Any, TextIO

import jsonpath_rw
import orjson
import pandas as pd

from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.source import FileProperty


def _unwrap_single_item(value: Any) -> Any:
    """Unwraps a single-item list to its value, or returns the value as is."""
    if isinstance(value, list) and len(value) == 1:
        if not value[0]:
            return None
        return value[0]
    return value


def parse_json_content(json_obj, fields):
    """Parsed all JSONs defined in the fields of RecordSet and outputs a pd.DF."""
    series = {}
    for field in fields:
        json_path = field.source.extract.json_path
        if not json_path:
            continue
        expr = jsonpath_rw.parse(json_path)
        vals = []
        for match in expr.find(json_obj):
            v = match.value
            # If we got back a one‐item list, unwrap it.
            if isinstance(v, list) and len(v) == 1:
                v = v[0]
            vals.append(v)
        series[json_path] = vals
    return pd.DataFrame(series)


class JsonReader:
    """Parser for JSON files, supporting both JSONPath and JMESPath expressions."""

    def __init__(self, fields: tuple[Field, ...]):
        """Initializes the parser with a tuple of Field objects.

        Args:
            fields (tuple[Field, ...]): A tuple of Field objects, each containing
            a source with a JSON path to extract.

        The constructor builds a list of tuples for each field with a valid
        JSON path:
            - The original JSON path string.
            - The engine used for evaluation ("jsonpath" for recursive-descent
              paths, "jmespath" for simple direct paths).
            - The compiled expression object for efficient evaluation.

        Fields without a JSON path are skipped.
        """
        import jmespath

        # Build a list of (original_jsonpath, engine, compiled_expr).
        self.exprs: list[tuple[str, str, Any]] = []
        for field in fields:
            json_path = field.source.extract.json_path
            if not json_path:
                continue

            # Decide whether this path can be JMESPath or needs full JSONPath.
            stripped = json_path.lstrip("$.")
            if ".." in json_path:
                # Uses recursive‐descent → fall back to jsonpath_ng.
                expr = jsonpath_rw.parse(json_path)
                engine = "jsonpath"
            else:
                # Simple direct path → use JMESPath.
                expr = jmespath.compile(stripped)
                engine = "jmespath"

            self.exprs.append((json_path, engine, expr))
        self.fields = fields

    def parse(self, fh: TextIO) -> pd.DataFrame:
        """Parses a JSON file-like object and extracts data into a pandas DataFrame.

        Args:
            fh (TextIO): A file-like object containing JSON data.

        Returns:
            pd.DataFrame: DataFrame with extracted data,
            where each column corresponds to an expression.
        """
        import orjson

        # Load entire JSON file (could be a list or a single dict).
        raw = fh.read()
        data = orjson.loads(raw)

        # Always treat as list of records.
        records = data if isinstance(data, list) else [data]

        series: dict[str, list] = {}
        for jp, engine, expr in self.exprs:
            vals: list = []
            for rec in records:
                if engine == "jmespath":
                    out = expr.search(rec)
                    # Unwrap single‐item lists.
                    if isinstance(out, list):
                        if len(out) == 1:
                            out = out[0]
                        elif len(out) == 0:
                            out = None
                else:  # Engine jsonpath_ng.
                    matches = expr.find(rec)
                    out = [m.value for m in matches]
                    if len(out) == 1:
                        out = out[0]
                    elif not out:
                        out = None

                # Flatten: if out is a list, extend; else append scalar (unless None).
                if isinstance(out, list):
                    vals.extend(out)
                elif out is not None:
                    vals.append(out)

            series[jp] = vals

        return pd.DataFrame(series)

    def raw(self, fh: TextIO) -> pd.DataFrame:
        """Reads a JSON file-like object and returns a single-cell pandas DataFrame.

        The entire JSON content is loaded and placed in a DataFrame with one row
        and one column, where the column name is specified by `FileProperty.content`.

        Args:
            fh (TextIO): A file-like object opened for reading JSON data.

        Returns:
            pd.DataFrame: A DataFrame containing the JSON content in a single cell.
        """
        # Raw JSON fallback: one‐cell DataFrame.
        raw = fh.read()
        content = orjson.loads(raw)
        return pd.DataFrame({FileProperty.content: [content]})


class JsonlReader:
    """Parser for JSON Lines files, supporting both JSONPath and JMESPath."""

    def __init__(self, fields):
        """Initializes the parser with a list of fields.

        Args:
            fields (list): A list of field objects, each expected to have a
            `source.extract.json_path` attribute.

        The constructor processes each field's JSON path:
            - If the path is a simple JSONPath (starts with "$." and does not
              contain ".."), it is converted to a JMESPath expression and
              compiled.
            - Otherwise, the path is parsed and compiled using jsonpath_rw.

        Compiled expressions, along with their original paths and the engine
        used, are stored in `self.exprs`. The original list of fields is stored
        in `self.fields`.
        """
        import jmespath

        self.exprs = []  # list of (orig_path, engine, compiled_expr)
        for field in fields:
            json_path = field.source.extract.json_path
            if not json_path:
                continue

            if json_path.startswith("$.") and ".." not in json_path:
                # simple JSONPath → JMESPath
                jm = json_path.lstrip("$.")  # drop the "$."
                expr = jmespath.compile(jm)
                engine = "jmespath"
            else:
                # anything with recursive‐descent or complex filters
                expr = jsonpath_rw.parse(json_path)
                engine = "jsonpath"

            self.exprs.append((json_path, engine, expr))
        self.fields = fields

    def parse(self, fh):
        """Parses a file-like object containing JSON objects (one per line).

        Args:
            fh: A file-like object to read from, where each line is a JSON object.

        Returns:
            pd.DataFrame: A DataFrame where each row corresponds to a parsed
            JSON object with extracted fields.

        Notes:
            - The extraction expressions are defined in self.exprs as tuples of
            (json_path, engine, expr).
            - For JMESPath, single-item lists are unwrapped to their value.
            - For JSONPath, values are extracted from Match objects and
            single-item lists are unwrapped.
        """
        import orjson

        rows = []
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = orjson.loads(line)
            row: dict[str, object] = {}
            for json_path, engine, expr in self.exprs:
                if engine == "jmespath":
                    out = expr.search(rec)
                    # Unwrap single‐item lists.
                    out = _unwrap_single_item(out)
                else:
                    matches = expr.find(rec)
                    temp = [m.value for m in matches]
                    # Unwrap single‐item lists.
                    out = _unwrap_single_item(temp)
                row[json_path] = out
            rows.append(row)
        return pd.DataFrame(rows)

    def raw(self, fh: TextIO) -> pd.DataFrame:
        """Reads a JSON Lines file-like object and returns a DataFrame."""
        fh.seek(0)
        return pd.read_json(fh, lines=True)
