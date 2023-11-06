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
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet
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


def _read_file(row) -> bytes:
    """Reads a binary file."""
    path = row[FileProperty.filepath]
    content = epath.Path(path).open("rb").read()
    return pd.Series({**row, FileProperty.content: content})


def _extract_lines(
    row,
) -> pd.Series:
    """Reads a file line-by-line and outputs a named pd.Series of the lines."""
    path = epath.Path(row[FileProperty.filepath])
    lines = path.open("rb").read().splitlines()
    return pd.Series(
        {**row, FileProperty.lines: lines, FileProperty.lineNumbers: range(len(lines))}
    )


def _extract_value(df: pd.DataFrame, field: Field) -> pd.DataFrame:
    """Extracts the value according to the field rules."""
    source = field.source
    print(field, source)
    column_name = source.get_field()
    if column_name in df:
        return df
    if source.extract.file_property == FileProperty.content:
        return df.apply(_read_file, axis=1)
    elif source.extract.file_property == FileProperty.lines:
        if FileProperty.lines in df:
            return df
        else:
            df = df.apply(_extract_lines, axis=1)
            return df.explode(
                column=[FileProperty.lines, FileProperty.lineNumbers], ignore_index=True
            )
    elif source.extract.file_property == FileProperty.lineNumbers:
        if FileProperty.lineNumbers in df:
            return df
        else:
            df = df.apply(_extract_lines, axis=1)
            return df.explode(
                column=[FileProperty.lines, FileProperty.lineNumbers], ignore_index=True
            )
    # else:
    #     assert False, "should not go here"
    #     possible_fields = list(df.axes if isinstance(df, pd.Series) else df.keys())
    #     assert column_name in df, (
    #         f'Column "{column_name}" does not exist. Inspect the ancestors of the field'
    #         f" {field} to understand why. Possible fields: {possible_fields}"
    #     )
    #     result = df[column_name]
    #     if isinstance(result, pd.Series):
    #         return result
    #     else:
    #         # This will be a one-line series. We need this to avoid e.g. dictionaries
    #         # to be converted to multi-line series:
    #         # pd.Series({"index": 1, "value": "a"}) -> index    1
    #         #                                          value    a
    #         # instead of:                                  0    {"index": 1, ...}
    #         return pd.Series(result, index=[0], copy=False)


@dataclasses.dataclass(frozen=True, repr=False)
class ReadField(Operation):
    """Reads a field from a Pandas DataFrame and applies transformations.

    ReadField.__call__() outputs a single-column pd.Series whose name is the field name.
    """

    node: RecordSet

    def __call__(self, df: pd.DataFrame) -> pd.Series:
        """See class' docstring."""
        # TROUVER COMMENT ITERER SUR TOUS LES FIELDS... I.E. SUB FIELDS
        fields: list[Field] = []
        for field in self.node.fields:
            if field.sub_fields:
                for sub_field in field.sub_fields:
                    fields.append(sub_field)
            else:
                fields.append(field)
        for field in fields:
            if not field.sub_fields:
                df = _extract_value(df, field)
        for _, row in df.iterrows():
            result: dict[str, Any] = {}
            for field in fields:
                source = field.source
                column = source.get_field()
                value = row[column]
                value = apply_transforms_fn(value, source=source)
                value = _cast_value(value, field.data_type)
                result[field.name] = value
            yield result
