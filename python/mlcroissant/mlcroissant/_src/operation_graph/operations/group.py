"""Group operation module."""

import dataclasses
from typing import Any, Dict, Iterator

import pandas as pd

from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet


@dataclasses.dataclass(frozen=True, repr=False)
class GroupRecordSetStart(Operation):
    """Starts the record set.

    This operation only forwards the argument from previous operations. It is useful in
    the graph of operations to mark a separation before ReadFields start.
    """

    node: RecordSet

    def __call__(self, df: pd.DataFrame) -> pd.DataFrame:
        """See class' docstring."""
        return df


class GroupRecordSetEnd(Operation):
    """Bundles all fields into a dictionary at the end."""

    node: RecordSet

    def _map_column_name(self, column_name: str) -> str:
        """Maps the column name from the previous name to the field's name if needed."""
        for field in self.node.fields:
            if field.source.extract.column == column_name:
                return field.name
        return column_name

    def __call__(self, *all_series: pd.DataFrame) -> Iterator[Dict[str, Any]]:
        """See class' docstring."""
        length = max([len(series) for series in all_series])
        index = pd.RangeIndex(length)
        all_series = list(all_series)
        for i, series in enumerate(all_series):
            # Forward fill one-line series to pad it to the target length.
            if len(series) == 1:
                all_series[i] = series.reindex(index, copy=False, method="ffill")
        df = pd.concat(all_series, axis=1, copy=False)
        for _, row in df.iterrows():
            result: dict[str, Any] = {}
            for column in df.columns:
                result[column] = row[column]
            yield result
