"""Group operation module."""

import dataclasses

from ml_croissant._src.operation_graph.base_operation import Operation
import pandas as pd


@dataclasses.dataclass(frozen=True, repr=False)
class GroupRecordSet(Operation):
    """Groups fields as a record set."""

    def __call__(self, *fields: pd.Series):
        concatenated_series = {k: v for field in fields for k, v in field.items()}
        return {self.node.name: concatenated_series}
