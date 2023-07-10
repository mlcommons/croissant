"""Merge operation module."""

import dataclasses

from ml_croissant._src.structure_graph.nodes import FileSet
from ml_croissant._src.operation_graph.base_operation import Operation
import pandas as pd


@dataclasses.dataclass(frozen=True, repr=False)
class Merge(Operation):
    """Merges several pd.DataFrame into one."""

    node: FileSet

    def __call__(self, *args: pd.DataFrame) -> pd.DataFrame:
        assert len(args) > 0, "No dataframe to merge."
        df = args[0]
        for other_df in args[1:]:
            df = df.merge(other_df)
        return df
