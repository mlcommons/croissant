"""Field operation module."""

import dataclasses
import io
from typing import Any

from etils import epath
import pandas as pd

from mlcroissant._src.core import constants
from mlcroissant._src.core.optional import deps
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.source import apply_transforms_fn
from mlcroissant._src.structure_graph.nodes.source import FileProperty


@dataclasses.dataclass(frozen=True, repr=False)
class ReadField(Operation):
    """Reads a field from a Pandas DataFrame and applies transformations."""

    node: Field

    def _cast_value(self, value: Any):
        data_type = self.node.data_type
        if pd.isna(value):
            return value
        elif data_type == constants.SCHEMA_ORG_DATA_TYPE_IMAGE_OBJECT:
            if isinstance(value, deps.PIL_Image.Image):
                return value
            elif isinstance(value, bytes):
                return deps.PIL_Image.open(io.BytesIO(value))
            else:
                raise ValueError(f"Type {type(value)} is not accepted for an image.")
        elif data_type == pd.Timestamp:
            # The date format is the first format found in the field's source.
            format = next(
                (
                    transform.format
                    for transform in self.node.source.transforms
                    if transform.format
                ),
                None,
            )
            return pd.to_datetime(value, format=format)
        elif not isinstance(data_type, type):
            raise ValueError(f"No special case for type {type(data_type)}.")
        try:
            return data_type(value)
        except ValueError as exception:
            raise ValueError(
                f'Expected type "{data_type}" for node "{self.node.uid}", but'
                f' got: "{type(value)}" with value "{value}"'
            ) from exception

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
        value = self._cast_value(value)
        return {self.node.name: value}
