"""Concatenate operation module."""

import dataclasses
import os

import pandas as pd

from mlcroissant._src.core.path import Path
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.structure_graph.nodes.file_set import FileSet
from mlcroissant._src.structure_graph.nodes.source import FileProperty


@dataclasses.dataclass(frozen=True, repr=False)
class Concatenate(Operation):
    """Concatenates several pd.DataFrames into one."""

    node: FileSet

    def __call__(self, *args: list[Path]) -> pd.DataFrame:
        """See class' docstring."""
        assert len(args) > 0, "No dataframe to merge."
        files = [file for files in args for file in files]
        return pd.DataFrame({
            FileProperty.filepath: [os.fspath(file.filepath) for file in files],
            FileProperty.filename: [file.filename for file in files],
            FileProperty.fullpath: [os.fspath(file.fullpath) for file in files],
        })
