"""Concatenate operation module."""

import dataclasses

import pandas as pd

from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.structure_graph.nodes.file_set import FileSet


@dataclasses.dataclass(frozen=True, repr=False)
class Concatenate(Operation):
    """Concatenates several pd.DataFrames into one."""

    node: FileSet

    def __call__(self, *args: pd.DataFrame) -> pd.DataFrame:
        """See class' docstring."""
        assert len(args) > 0, "No dataframe to merge."
        return pd.concat(args)
