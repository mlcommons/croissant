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

    def __call__(self, *series: pd.Series):
        """See class' docstring."""
        df = pd.DataFrame({value.name: value for value in series})
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
