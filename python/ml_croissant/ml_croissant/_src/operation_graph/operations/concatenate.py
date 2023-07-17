"""Concatenate operation module."""

import dataclasses

from ml_croissant._src.structure_graph.nodes import FileSet
from ml_croissant._src.operation_graph.base_operation import Operation
import pandas as pd


@dataclasses.dataclass(frozen=True, repr=False)
class Concatenate(Operation):
    """Concatenates several pd.DataFrames into one."""

    node: FileSet

    def __call__(self, *args: pd.DataFrame) -> pd.DataFrame:
        """See class' docstring."""
        assert len(args) > 0, "No dataframe to merge."
        return pd.concat(args)
