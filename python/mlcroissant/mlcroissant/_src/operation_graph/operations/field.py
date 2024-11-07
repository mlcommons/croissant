"""Field operation module."""

import dataclasses
import functools
import io
import logging
import os
import pathlib
import re
from typing import Any, Iterator

from etils import epath
import jsonpath_rw
import numpy as np
import pandas as pd
from rdflib import term

from mlcroissant._src.core.constants import DataType
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.ml import bounding_box
from mlcroissant._src.core.optional import deps
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet
from mlcroissant._src.structure_graph.nodes.source import FileProperty
from mlcroissant._src.structure_graph.nodes.source import Transform


@functools.cache
def _parse_jsonpath(json_path: str):
    """Memoizes jsonpath_rw.parse for better performances."""
    return jsonpath_rw.parse(json_path)


def _is_repeated_field(field: Field | None) -> bool | None:
    return isinstance(field, Field) and field.repeated


def _apply_transform_fn(value: Any, transform: Transform, field: Field) -> Any:
    """Applies one transform to `value`."""
    if _is_na(value):
        return value
    if transform.regex is not None:
        source_regex = re.compile(transform.regex)
        if isinstance(value, pathlib.PurePath):
            value = os.fspath(value)
        match = source_regex.match(value)
        if match is None:
            logging.warning(f"Could not match {source_regex} in {value}")
            return value
        for group in match.groups():
            if group is not None:
                return group
    elif transform.json_path is not None:
        jsonpath_expression = _parse_jsonpath(transform.json_path)
        return next(match.value for match in jsonpath_expression.find(value))
    elif transform.format is not None:
        if field.data_type is pd.Timestamp:
            return pd.Timestamp(value).strftime(transform.format)
        else:
            raise ValueError(f"`format` only applies to dates. Got {field.data_type}")
    elif transform.separator is not None:
        return value.split(transform.separator)
    return value


def apply_transforms_fn(value: Any, field: Field, repeated: bool = False) -> Any:
    """Applies all transforms in `source` to `value`."""
    source = field.source
    if source is None:
        return value
    transforms = source.transforms
    for transform in transforms:
        if repeated and isinstance(value, (list, np.ndarray)):
            value = [_apply_transform_fn(v, transform, field) for v in value]
        else:
            value = _apply_transform_fn(value, transform, field)
    return value


def _is_na(value: Any) -> bool:
    return not isinstance(value, (list, np.ndarray)) and pd.isna(value)


def _cast_value(ctx: Context, value: Any, data_type: type | term.URIRef | None):
    """Casts the value `value` to the desired target data type `data_type`."""
    if _is_na(value):
        return value
    elif data_type == DataType.IMAGE_OBJECT:
        if isinstance(value, deps.PIL_Image.Image):
            return value
        elif isinstance(value, bytes):
            return deps.PIL_Image.open(io.BytesIO(value))
        else:
            raise ValueError(f"Type {type(value)} is not accepted for an image.")
    elif data_type == DataType.AUDIO_OBJECT:
        output = deps.librosa.load(io.BytesIO(value))
        return output
    elif data_type == DataType.BOUNDING_BOX:  # pytype: disable=wrong-arg-types
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
    elif isinstance(value, int) or isinstance(value, float):
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


def _populate_repeated_nested_subfield(
    value: Any, field: Field, result: dict[str, Any]
) -> dict[str, Any]:
    """Populates result with a field's nested subfields."""
    if not field.parent:
        raise ValueError(
            "Nested subfields can only be populated when the parent field exists!"
        )
    parent_id = field.parent.id
    existing_values = result.get(parent_id, None)
    if existing_values:
        if not _is_na(value) and len(value) != len(existing_values):
            raise ValueError(
                f"Lenghts of {field.id} doesn't match  already stored items for "
                f" {parent_id}"
            )
        for i in range(len(existing_values)):
            existing_values[i][field.id] = None if _is_na(value) else value[i]
    else:
        result[parent_id] = (
            [{field.id: None}] if _is_na(value) else [{field.id: v} for v in value]
        )
    return result


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

    def call(self, df: pd.DataFrame) -> Iterator[dict[str, Any]]:
        """See class' docstring."""
        if self.node.data:
            # The RecordSet has `data`, so we directly yield from the dataframe.
            for _, row in df.iterrows():
                yield dict(row)
            return
        fields = self._fields()
        for field in fields:
            df = _extract_value(df, field)

        def _get_result(row):
            """Returns a record parsed as a dictionary of fields."""
            result: dict[str, Any] = {}
            for field in fields:
                source = field.source
                column = source.get_column()
                assert column in df, (
                    f'Column "{column}" does not exist. Inspect the ancestors of the'
                    f" field {field} to understand why. Possible fields: {df.columns}"
                )
                is_repeated = field.repeated or (
                    field.parent and _is_repeated_field(field.parent)
                )
                value = apply_transforms_fn(
                    row[column], field=field, repeated=is_repeated
                )
                if _is_na(value):
                    value = None
                elif is_repeated:
                    value = [
                        _cast_value(self.node.ctx, v, field.data_type) for v in value
                    ]
                else:
                    value = _cast_value(self.node.ctx, value, field.data_type)

                if self.node.ctx.is_v0():
                    result[field.name] = value
                else:
                    if field in self.node.fields:
                        result[field.id] = value
                    else:
                        # Repeated nested sub-fields render as a list of dictionaries.
                        if field.parent:
                            if _is_repeated_field(field.parent):
                                result = _populate_repeated_nested_subfield(
                                    value=value, field=field, result=result
                                )
                            # Non-repeated subfields render as a single dictionary.
                            else:
                                if field.parent.id not in result:
                                    result[field.parent.id] = {}
                                result[field.parent.id][field.id] = value
                        else:
                            raise ValueError(
                                f"The field {field.id} is a SubField but has no parent."
                            )
            return result

        chunk_size = 100
        for i in range(0, len(df), chunk_size):
            yield from df[i : i + chunk_size].apply(_get_result, axis=1)
