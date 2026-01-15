"""Filter operation module."""

import dataclasses
import fnmatch
import functools
import os
import pathlib
import re
import types

from etils import epath

from mlcroissant._src.core.path import get_fullpath
from mlcroissant._src.core.path import Path
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.structure_graph.nodes.file_set import FileSet


@functools.cache
def _memoized_regex(pattern: str) -> re.Pattern:
    regex = fnmatch.translate(pattern)
    return re.compile(regex)


def match_path(patterns: list[str] | None, path: pathlib.PurePath) -> bool:
    """Returns True if at least one pattern matches path."""
    if not patterns:
        return True
    for pattern in patterns:
        regex = _memoized_regex(pattern)
        if regex.match(os.fspath(path)):
            return True
    return False


@dataclasses.dataclass(frozen=True, repr=False)
class FilterFiles(Operation):
    """Filters files within a FileSet given a glob pattern."""

    node: FileSet

    def call(self, *paths: Path) -> list[Path]:
        """See class' docstring."""
        if self.node.includes is None:
            raise ValueError("cannot filter files without `includes`.")
        included_files: list[Path] = []
        for path in paths:
            if isinstance(path, types.GeneratorType):
                for p in path:
                    if p.filepath.exists() and p.filepath.is_dir():
                        for basepath, _, files in p.filepath.walk():
                            for file in files:
                                filepath = epath.Path(basepath) / file
                                fullpath = get_fullpath(filepath, p.filepath)
                                match_includes = match_path(self.node.includes, fullpath)
                                if match_includes:
                                    included_files.append(
                                        Path(
                                            filepath=filepath,
                                            fullpath=fullpath,
                                        )
                                    )
                    else:
                        match_includes = match_path(self.node.includes, p.fullpath)
                        if match_includes:
                            included_files.append(p)
            else:
                # If the file is a directory, we walk it.
                if path.filepath.exists() and path.filepath.is_dir():
                    for basepath, _, files in path.filepath.walk():  # type: ignore  # https://github.com/python/mypy/issues/11880
                        for file in files:
                            filepath = epath.Path(basepath) / file
                            fullpath = get_fullpath(filepath, path.filepath)
                            match_includes = match_path(self.node.includes, fullpath)
                            if match_includes:
                                included_files.append(
                                    Path(
                                        filepath=filepath,
                                        fullpath=fullpath,
                                    )
                                )
                # If the file is a file, we directly check if it matches the includes.
                else:
                    match_includes = match_path(self.node.includes, path.fullpath)
                    if match_includes:
                        included_files.append(path)
        # We need to sort `files` to have a deterministic/reproducible order.
        included_files.sort()
        return sorted(included_files)
