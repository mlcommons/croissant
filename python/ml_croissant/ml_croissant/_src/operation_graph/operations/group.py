"""Group operation module."""

import dataclasses

import pandas as pd

from ml_croissant._src.operation_graph.base_operation import Operation


@dataclasses.dataclass(frozen=True, repr=False)
class GroupRecordSet(Operation):
    """Groups fields as a record set."""

    def __call__(self, *fields: pd.Series):
        """See class' docstring."""
        concatenated_series = {k: v for field in fields for k, v in field.items()}
        return concatenated_series
