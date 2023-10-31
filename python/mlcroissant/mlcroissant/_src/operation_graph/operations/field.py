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


def _extract_value(df: pd.DataFrame, field: Field) -> Any:
    """Extracts the value according to the field rules."""
    source = field.source
    if source.extract.file_property == FileProperty.content:
        filepath = df[FileProperty.filepath]
        with epath.Path(filepath).open("rb") as f:
            return f.read()
    elif source.extract.file_property == FileProperty.lines:
        if FileProperty.lines in df:
            return df[FileProperty.lines]
        else:
            filepath = df[FileProperty.filepath]
            return pd.read_csv(filepath, header=None, names=[field.name])[field.name]
    else:
        column_name = source.get_field()
        possible_fields = list(df.axes if isinstance(df, pd.Series) else df.keys())
        assert (
            column_name in df
        ), f'Field "{column_name}" does not exist. Possible fields: {possible_fields}'
        return df[column_name]


def _convert_to_series(value: Any, field: Field) -> pd.Series:
    """Converts `value` to a pd.Series even if it has one line."""
    if isinstance(value, pd.Series):
        return value
    else:
        return pd.Series([value], name=field.name)


@dataclasses.dataclass(frozen=True, repr=False)
class ReadField(Operation):
    """Reads a field from a Pandas DataFrame and applies transformations.

    ReadField.__call__() outputs a single-column pd.Series whose name is the field name.
    """

    node: Field

    def __call__(self, df: pd.DataFrame) -> pd.Series:
        """See class' docstring."""
        value = _extract_value(df, self.node)
        series = _convert_to_series(value, self.node)
        transforms = functools.partial(apply_transforms_fn, source=self.node.source)
        cast = functools.partial(_cast_value, data_type=self.node.data_type)
        return series.apply(transforms).apply(cast)
