"""Filter operation module."""

import dataclasses
import fnmatch
import os
import re

from etils import epath

from mlcroissant._src.core.path import get_fullpath
from mlcroissant._src.core.path import Path
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.structure_graph.nodes.file_set import FileSet


@dataclasses.dataclass(frozen=True, repr=False)
class FilterFiles(Operation):
    """Filters files within a FileSet given a glob pattern."""

    node: FileSet

    def __call__(self, *paths: Path) -> list[Path]:
        """See class' docstring."""
        if self.node.includes is None:
            raise ValueError("cannot filter files without `includes`.")
        includes = fnmatch.translate(self.node.includes)
        includes_re = re.compile(includes)
        included_files: list[Path] = []
        for path in paths:
            path = os.fspath(path.filepath)
            for basepath, _, files in os.walk(path):  # type: ignore  # https://github.com/python/mypy/issues/11880
                for file in files:
                    filepath = epath.Path(basepath) / file
                    fullpath = get_fullpath(filepath, epath.Path(path))
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
