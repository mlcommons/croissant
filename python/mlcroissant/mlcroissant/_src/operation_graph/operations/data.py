"""Data operation module."""

import dataclasses

import pandas as pd

from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet


@dataclasses.dataclass(frozen=True, repr=False)
class Data(Operation):
    """Operation for inline data."""

    node: RecordSet

    def __call__(self, *args) -> pd.DataFrame:
        """See class' docstring."""
        del args  # unused
        return pd.DataFrame.from_records(self.node.data)
