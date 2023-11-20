"""Field operation module."""

import dataclasses
import io
from typing import Any, Iterator

from etils import epath
import numpy as np
import pandas as pd
from rdflib import term

from mlcroissant._src.core.constants import DataType
from mlcroissant._src.core.ml import bounding_box
from mlcroissant._src.core.optional import deps
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet
from mlcroissant._src.structure_graph.nodes.source import apply_transforms_fn
from mlcroissant._src.structure_graph.nodes.source import FileProperty


def _cast_value(value: Any, data_type: type | term.URIRef | None):
    """Casts the value `value` to the desired target data type `data_type`."""
    is_na = not isinstance(value, (list, np.ndarray)) and pd.isna(value)
    if is_na:
        return value
    elif data_type == DataType.IMAGE_OBJECT:
        if isinstance(value, deps.PIL_Image.Image):
            return value
        elif isinstance(value, bytes):
            return deps.PIL_Image.open(io.BytesIO(value))
        else:
            raise ValueError(f"Type {type(value)} is not accepted for an image.")
    elif data_type == DataType.BOUNDING_BOX:
        return bounding_box.parse(value)
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


def _read_file(row: pd.Series) -> pd.Series:
    """Reads a binary file."""
    path = row[FileProperty.filepath]
    content = epath.Path(path).open("rb").read()
    return pd.Series({**row, FileProperty.content: content})


def _extract_lines(row: pd.Series) -> pd.Series:
    """Reads a file line-by-line and outputs a named pd.Series of the lines."""
    path = epath.Path(row[FileProperty.filepath])
    lines = path.open("rb").read().splitlines()
    return pd.Series({
        **row, FileProperty.lines: lines, FileProperty.lineNumbers: range(len(lines))
    })


def _extract_value(df: pd.DataFrame, field: Field) -> pd.DataFrame:
    """Extracts the value according to the field rules."""
    source = field.source
    column_name = source.get_column()
    if column_name in df:
        return df
    elif source.extract.file_property == FileProperty.content:
        return df.apply(_read_file, axis=1)
    elif source.extract.file_property in [FileProperty.lines, FileProperty.lineNumbers]:
        df = df.apply(_extract_lines, axis=1)
        return df.explode(
            column=[FileProperty.lines, FileProperty.lineNumbers], ignore_index=True
        )
    return df


@dataclasses.dataclass(frozen=True, repr=False)
class ReadFields(Operation):
    """Reads fields in a RecordSet from a Pandas DataFrame and applies transformations.

    ReadFields.__call__() yields dict-shaped records with the proper transformations,
    types and name.
    """

    node: RecordSet

    def _fields(self) -> list[Field]:
        """Extracts all fields (i.e., direct fields without subFields and subFields)."""
        fields: list[Field] = []
        for field in self.node.fields:
            if field.sub_fields:
                for sub_field in field.sub_fields:
                    fields.append(sub_field)
            else:
                fields.append(field)
        return fields

    def __call__(self, df: pd.DataFrame) -> Iterator[dict[str, Any]]:
        """See class' docstring."""
        fields = self._fields()
        for field in fields:
            df = _extract_value(df, field)
        for _, row in df.iterrows():
            result: dict[str, Any] = {}
            for field in fields:
                source = field.source
                column = source.get_column()
                assert column in df, (
                    f'Column "{column}" does not exist. Inspect the ancestors of the'
                    f" field {field} to understand why. Possible fields: {df.columns}"
                )
                value = row[column]
                value = apply_transforms_fn(value, field=field)
                value = _cast_value(value, field.data_type)
                result[field.name] = value
            yield result
