"""Field operation module."""

import dataclasses
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


@dataclasses.dataclass(frozen=True, repr=False)
class ReadField(Operation):
    """Reads a field from a Pandas DataFrame and applies transformations."""

    node: Field

    def __call__(self, series: pd.Series):
        """See class' docstring."""
        source = self.node.source
        if source.extract.file_property == FileProperty.content:
            filepath = series[FileProperty.filepath]
            with epath.Path(filepath).open("rb") as f:
                value = f.read()
        else:
            field = source.get_field()
            possible_fields = list(
                series.axes if isinstance(series, pd.Series) else series.keys()
            )
            assert (
                field in series
            ), f'Field "{field}" does not exist. Possible fields: {possible_fields}'
            value = series[field]
        value = apply_transforms_fn(value, self.node.source)
        try:
            value = _cast_value(value, self.node.data_type)
        except ValueError as exception:
            raise ValueError(
                f'Expected type "{self.node.data_type}" for node "{self.node.uid}", but'
                f' got: "{type(value)}" with value "{value}"'
            ) from exception
        return {self.node.name: value}
