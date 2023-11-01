"""Group operation module."""

import dataclasses
from typing import Any

import pandas as pd

from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet


@dataclasses.dataclass(frozen=True, repr=False)
class GroupRecordSetStart(Operation):
    """Groups fields as a record set."""

    node: RecordSet

    def __call__(self, *all_series: pd.Series):
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


class GroupRecordSetEnd(Operation):
    """Gathers all records at the end."""

    node: RecordSet

    def __call__(self, *args: pd.DataFrame) -> pd.DataFrame:
        """See class' docstring."""
        if not args:
            raise ValueError("Empty RecordSet yielded 0 pd.DataFrame.")
        return args[0]
