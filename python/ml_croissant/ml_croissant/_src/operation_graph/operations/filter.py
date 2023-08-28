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
class FilterFiles(Operation):
    """Filters files within a FileSet given a glob pattern."""

    node: FileSet

    def __call__(self, *dirs: Path) -> list[Path]:
        """See class' docstring."""
        includes = fnmatch.translate(self.node.includes)
        includes_re = re.compile(includes)
        included_files: list[epath.Path] = []
        for dir_ in dirs:
            dir_ = os.fspath(dir_.filepath)
            for basepath, _, files in os.walk(dir_):
                for file in files:
                    filepath = epath.Path(basepath) / file
                    fullpath = get_fullpath(filepath, dir_)
                    if includes_re.match(os.fspath(fullpath)):
                        included_files.append(
                            Path(
                                filepath=filepath,
                                fullpath=fullpath,
                            )
                        )
        # We need to sort `files` to have a deterministic/reproducible order.
        included_files.sort()
        return sorted(included_files)
