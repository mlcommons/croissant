"""Join operation module."""

import dataclasses

import pandas as pd

from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.operation_graph.operations.field import apply_transforms_fn
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet
from mlcroissant._src.structure_graph.nodes.source import get_parent_uid
from mlcroissant._src.structure_graph.nodes.source import Source


@dataclasses.dataclass(frozen=True, repr=False)
class Join(Operation):
    """Joins pd.DataFrames."""

    node: RecordSet

    def __call__(self, *args: pd.Series) -> pd.Series | None:
        """See class' docstring."""
        if len(args) == 1:
            return args[0]
        predecessors: list[str] = [
            operation.node.uid for operation in self.operations.predecessors(self)
        ]
        if len(predecessors) != len(args):
            raise ValueError(f"Unsupported: Trying to join {len(args)} pd.DataFrames.")
        fields = self.node.fields
        # `joins` is the list of joins: field x (source1, df1) x (source2, df2)
        joins: list[
            tuple[Field, tuple[Source, pd.Series], tuple[Source, pd.Series]]
        ] = []
        for field in fields:
            left = field.source
            right = field.references
            if left is None or right is None:
                continue
            if left.uid is None or right.uid is None:
                continue
            left_index = predecessors.index(get_parent_uid(left.uid))
            right_index = predecessors.index(get_parent_uid(right.uid))
            join = (field, (left, args[left_index]), (right, args[right_index]))
            if join not in joins:
                joins.append(join)
        for field, (left, df_left), (right, df_right) in joins:
            assert left is not None and left.uid is not None, (
                f'Left reference for "{field.uid}" is None. It should be a valid'
                " reference."
            )
            assert right is not None and right.uid is not None, (
                f'Right reference for "{field.uid}" is None. It should be a valid'
                " reference."
            )
            left_column = left.get_column()
            right_column = right.get_column()
            assert left_column in df_left.columns, (
                f'Column "{left_column}" does not exist in node "{left.uid}".'
                f" Existing columns: {df_left.columns}"
            )
            assert right_column in df_right.columns, (
                f'Column "{right_column}" does not exist in node "{right.uid}".'
                f" Existing columns: {df_right.columns}"
            )
            df_left[left_column] = df_left[left_column].transform(
                apply_transforms_fn, field=field
            )
            return df_left.merge(
                df_right,
                left_on=left_column,
                right_on=right_column,
                how="left",
                suffixes=(None, "_right"),
            )
        return None
