"""Join operation module."""

from typing import Union

import dataclasses

import pandas as pd

from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet
from mlcroissant._src.structure_graph.nodes.source import apply_transforms_fn


@dataclasses.dataclass(frozen=True, repr=False)
class Join(Operation):
    """Joins pd.DataFrames."""

    node: RecordSet

    def __call__(self, *args: pd.Series) -> Union[pd.Series, None]:
        """See class' docstring."""
        if len(args) == 1:
            return args[0]
        elif len(args) == 2:
            fields = self.node.fields
            joins = set()
            for field in fields:
                left = field.source
                right = field.references
                if left and right and (left, right) not in joins:
                    joins.add((left, right))
            for left, right in joins:
                assert left is not None and left.uid is not None, (
                    f'Left reference for "{field.uid}" is None. It should be a valid'
                    " reference."
                )
                assert right is not None and right.uid is not None, (
                    f'Right reference for "{field.uid}" is None. It should be a valid'
                    " reference."
                )
                left_key = left.get_field()
                right_key = right.get_field()
                # A priori, we cannot know which one is left and which one is right,
                # because topological sort is not reproducible in some case.
                df_left, df_right = args
                if left_key not in df_left.columns or right_key not in df_right.columns:
                    df_left, df_right = df_right, df_left
                assert left_key in df_left.columns, (
                    f'Column "{left_key}" does not exist in node "{left.uid}".'
                    f" Existing columns: {df_left.columns}"
                )
                assert right_key in df_right.columns, (
                    f'Column "{right_key}" does not exist in node "{right.uid}".'
                    f" Existing columns: {df_right.columns}"
                )
                df_left[left_key] = df_left[left_key].transform(
                    apply_transforms_fn, source=left
                )
                return df_left.merge(
                    df_right,
                    left_on=left_key,
                    right_on=right_key,
                    how="left",
                    suffixes=(None, "_right"),
                )
        else:
            raise NotImplementedError(
                f"Unsupported: Trying to join {len(args)} pd.DataFrames."
            )
