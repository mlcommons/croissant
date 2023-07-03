"""Data operation module."""

import dataclasses

from ml_croissant._src.structure_graph.nodes import Field
from ml_croissant._src.operation_graph.base_operation import Operation
import pandas as pd


@dataclasses.dataclass(frozen=True, repr=False)
class Data(Operation):
    node: Field

    def __call__(self):
        return pd.DataFrame(self.node.data)
