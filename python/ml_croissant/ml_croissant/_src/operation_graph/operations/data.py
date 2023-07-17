"""Data operation module."""

import dataclasses
import json

from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.structure_graph.nodes import RecordSet
import pandas as pd


@dataclasses.dataclass(frozen=True, repr=False)
class Data(Operation):
    """Operation for inline data."""

    node: RecordSet

    def __call__(self):
        """See class' docstring."""
        return pd.DataFrame.from_records(json.loads(self.node.data))
