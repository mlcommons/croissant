"""Field operation module."""

import dataclasses
from typing import Any

from etils import epath
from ml_croissant._src.core.data_types import EXPECTED_DATA_TYPES
from ml_croissant._src.structure_graph.nodes import Field
from ml_croissant._src.operation_graph.base_operation import Operation
import pandas as pd
from rdflib import namespace


@dataclasses.dataclass(frozen=True, repr=False)
class ReadField(Operation):
    """Reads a field from a Pandas DataFrame and applies transformations."""

    node: Field
    rdf_namespace_manager: namespace.NamespaceManager
    field: str | None = None

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
            data_type = data_types
            if data_type not in EXPECTED_DATA_TYPES:
                raise ValueError(
                    f'Unknown data type "{data_type}" found for "{self.node.uid}".'
                    f' Possible types: {", ".join(EXPECTED_DATA_TYPES)}.'
                )
            return EXPECTED_DATA_TYPES[data_type]
        raise ValueError(f'No data type found for "{self.node.uid}"')

    def _cast_value(self, value: Any):
        data_type = self.find_data_type(self.node.data_type)
        if pd.isna(value):
            return value
        elif data_type == pd.Timestamp:
            # The date format is the first format found in the field's source.
            format = next(
                (
                    transform.format
                    for transform in self.node.source.apply_transform
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
        if self.field is None:
            assert len(self.node.source.reference) == 2, (
                f'Node "{self.node.uid}" refers to a wrong reference in its source:'
                f" {self.node.source}."
            )
            field = self.node.source.reference[1]
        else:
            field = self.field
        if field == "content":
            filepath = series["filepath"]
            with epath.Path(filepath).open("rb") as f:
                value = f.read()
        else:
            assert field in series, (
                f'Field "{field}" does not exist. Possible fields:'
                f" {list(series.axes) if isinstance(series, pd.Series) else series.keys()}"
            )
            value = series[field]
            value = self._cast_value(value)
        return {self.node.name: value}
