"""Field operation module."""

import dataclasses
import io
from typing import Any

from etils import epath
import pandas as pd
from rdflib import term

from ml_croissant._src.core import constants
from ml_croissant._src.core.data_types import EXPECTED_DATA_TYPES
from ml_croissant._src.core.optional import deps
from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.structure_graph.nodes.field import Field
from ml_croissant._src.structure_graph.nodes.source import apply_transforms_fn
from ml_croissant._src.structure_graph.nodes.source import FileProperty


@dataclasses.dataclass(frozen=True, repr=False)
class ReadField(Operation):
    """Reads a field from a Pandas DataFrame and applies transformations."""

    node: Field

    def find_data_type(self, data_types: list[str] | tuple[str, ...] | str) -> type:
        """Finds the data type by expanding its name from the namespace manager.

        In some cases, we specify a list of data types. In that case, we take the first
        one in the list that can be parsed.
        """
        if isinstance(data_types, (list, tuple)):
            for data_type in data_types:
                try:
                    return self.find_data_type(data_type)
                except ValueError:
                    continue
        elif isinstance(data_types, str):
            data_type = term.URIRef(data_types)
            if data_type not in EXPECTED_DATA_TYPES:
                raise ValueError(
                    f'Unknown data type "{data_type}" found for "{self.node.uid}".'
                    f' Possible types: {", ".join(EXPECTED_DATA_TYPES)}.'
                )
            return EXPECTED_DATA_TYPES[data_type]
        raise ValueError(
            f'No data type found for "{self.node.uid}". Possible types:'
            f' {", ".join(EXPECTED_DATA_TYPES)}'
        )

    def _cast_value(self, value: Any):
        data_type = self.find_data_type(self.node.actual_data_type)
        if pd.isna(value):
            return value
        elif data_type == constants.SCHEMA_ORG_DATA_TYPE_IMAGE_OBJECT:
            # TODO(https://github.com/mlcommons/croissant/issues/199): this is
            # temporary.For now, we only accept dictionary {"bytes": b"\x89PNG\r\n..."}.
            if "bytes" not in value:
                raise ValueError("reading images expects a dict with a `bytes` key.")
            return deps.PIL_Image.open(io.BytesIO(value["bytes"]))
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
            value = self._cast_value(value)
        value = apply_transforms_fn(value, self.node.source)
        return {self.node.name: value}
