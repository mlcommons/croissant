"""Field operation module."""

import dataclasses
import functools
import io
from typing import Any

from etils import epath
import pandas as pd
from rdflib import term

from mlcroissant._src.core.constants import DataType
from mlcroissant._src.core.optional import deps
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.source import apply_transforms_fn
from mlcroissant._src.structure_graph.nodes.source import FileProperty


def _cast_value(value: Any, data_type: type | term.URIRef | None):
    """Casts the value `value` to the desired target data type `data_type`."""
    if pd.isna(value):
        return value
    elif data_type == DataType.IMAGE_OBJECT:
        if isinstance(value, deps.PIL_Image.Image):
            return value
        elif isinstance(value, bytes):
            return deps.PIL_Image.open(io.BytesIO(value))
        else:
            raise ValueError(f"Type {type(value)} is not accepted for an image.")
    elif not isinstance(data_type, type):
        raise ValueError(f"No special case for type {data_type}.")
    elif data_type == bytes and not isinstance(value, bytes):
        return _to_bytes(value)
    else:
        return data_type(value)


def _to_bytes(value: Any) -> bytes:
    """Casts the value `value` to bytes."""
    if isinstance(value, bytes):
        return value
    elif isinstance(value, str):
        return value.encode("utf-8")
    elif isinstance(value, int):
        return str(value).encode("utf-8")
    else:
        return bytes(value)


def _read_file(path: epath.PathLike) -> bytes:
    """Reads a binary file."""
    return epath.Path(path).open("rb").read()


def _extract_lines(
    path: epath.PathLike,
    name: str,
) -> pd.Series:
    """Reads a file line-by-line and outputs a named pd.Series of the lines."""
    path = epath.Path(path)
    lines = path.open("rb").read().splitlines()
    return pd.Series(lines, name=name)


def _extract_line_numbers(
    path: epath.PathLike,
    name: str,
) -> pd.Series:
    """Reads a file line-by-line and outputs a named pd.Series of the lines."""
    lines = _extract_lines(path, name)
    return pd.Series(range(len(lines)), name=name)


def _extract_value(df: pd.DataFrame, field: Field) -> pd.Series:
    """Extracts the value according to the field rules."""
    source = field.source
    if source.extract.file_property == FileProperty.content:
        return df[FileProperty.filepath].apply(_read_file).T[0]
    elif source.extract.file_property == FileProperty.lines:
        if FileProperty.lines in df:
            return df[FileProperty.lines]
        else:
            series = df[FileProperty.filepath]
            return series.apply(_extract_lines, name=field.name).T[0]
    elif source.extract.file_property == FileProperty.lineNumbers:
        if FileProperty.lineNumbers in df:
            return df[FileProperty.lineNumbers]
        else:
            series = df[FileProperty.filepath]
            return series.apply(_extract_line_numbers, name=field.name).T[0]
    else:
        column_name = source.get_field()
        possible_fields = list(df.axes if isinstance(df, pd.Series) else df.keys())
        assert column_name in df, (
            f'Column "{column_name}" does not exist. Inspect the ancestors of the field'
            f" {field} to understand why. Possible fields: {possible_fields}"
        )
        result = df[column_name]
        if isinstance(result, pd.Series):
            return result
        else:
            # This will be a one-line series. We need this to avoid e.g. dictionaries
            # to be converted to multi-line series:
            # pd.Series({"index": 1, "value": "a"}) -> index    1
            #                                          value    a
            # instead of:                                  0    {"index": 1, ...}
            return pd.Series(result, index=[0], copy=False)


def _name_series(series: pd.Series, field: Field) -> pd.Series:
    """Names the series without copying it."""
    return pd.Series(series, name=field.name, copy=False)


@dataclasses.dataclass(frozen=True, repr=False)
class ReadField(Operation):
    """Reads a field from a Pandas DataFrame and applies transformations.

    ReadField.__call__() outputs a single-column pd.Series whose name is the field name.
    """

    node: Field

    def __call__(self, df: pd.DataFrame) -> pd.Series:
        """See class' docstring."""
        value = _extract_value(df, self.node)
        series = _name_series(value, self.node)
        transforms = functools.partial(apply_transforms_fn, source=self.node.source)
        cast = functools.partial(_cast_value, data_type=self.node.data_type)
        # PyType mistakenly infers the return type as `Any`.
        return series.apply(transforms).apply(cast)  # pytype: disable=bad-return-type
