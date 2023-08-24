"""Filter operation module."""

import dataclasses
import fnmatch
import os
import re

from etils import epath

from ml_croissant._src.core.path import get_fullpath
from ml_croissant._src.core.path import Path
from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.structure_graph.nodes.file_set import FileSet


@dataclasses.dataclass(frozen=True, repr=False)
class Filter(Operation):
    """Filters within a FileSet."""

    node: FileSet

    def __call__(self, *dirs: Path) -> list[Path]:
        """See class' docstring."""
        includes = fnmatch.translate(self.node.includes)
        included_files: list[epath.Path] = []
        for dir_ in dirs:
            dir_ = os.fspath(dir_.filepath)
            for basepath, _, files in os.walk(dir_):
                for file in files:
                    filepath = epath.Path(basepath) / file
                    fullpath = get_fullpath(filepath, dir_)
                    if re.match(includes, fullpath):
                        included_files.append(
                            Path(
                                filepath=filepath,
                                fullpath=fullpath,
                            )
                        )
        # We need to sort `files` to have a deterministic/reproducible order.
        included_files.sort()
        return sorted(included_files)
