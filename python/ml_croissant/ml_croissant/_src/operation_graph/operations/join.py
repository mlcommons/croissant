"""Join operation module."""

import dataclasses

from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.structure_graph.nodes import Source
from ml_croissant._src.structure_graph.nodes.source import apply_transforms_fn
import pandas as pd


@dataclasses.dataclass(frozen=True, repr=False)
class Join(Operation):
    """Joins pd.DataFrames."""

    def __call__(
        self, *args: pd.Series, left: Source | None = None, right: Source | None = None
    ) -> pd.Series:
        """See class' docstring."""
        if len(args) == 1:
            return args[0]
        elif len(args) == 2:
            assert left is not None and left.reference is not None, (
                f'Left reference for "{self.node.uid}" is None. It should be a valid'
                " reference."
            )
            assert right is not None and right.reference is not None, (
                f'Right reference for "{self.node.uid}" is None. It should be a valid'
                " reference."
            )
            left_key = left.reference[1]
            right_key = right.reference[1]
            # A priori, we cannot know which one is left and which one is right, because
            # topological sort is not reproducible in some case.
            df_left, df_right = args
            if left_key not in df_left.columns or right_key not in df_right.columns:
                df_left, df_right = df_right, df_left
            assert (
                len(left.reference) == 2
            ), "JOIN operation does not define a column name."
            assert left_key in df_left.columns, (
                f'Column "{left_key}" does not exist in node "{left.reference[0]}".'
                f" Existing columns: {df_left.columns}"
            )
            assert right_key in df_right.columns, (
                f'Column "{right_key}" does not exist in node "{right.reference[0]}".'
                f" Existing columns: {df_right.columns}"
            )
            df_left[left_key] = df_left[left_key].transform(
                apply_transforms_fn, source=left
            )
            return df_left.merge(
                df_right, left_on=left_key, right_on=right_key, how="left"
            )
        else:
            raise NotImplementedError(
                f"Unsupported: Trying to joing {len(args)} pd.DataFrames."
            )
