"""ReadLines operation module."""

import dataclasses

import pathlib

from etils import epath
from mlcroissant._src.core.path import Path
from mlcroissant._src.operation_graph.base_operation import Operation


@dataclasses.dataclass(frozen=True, repr=False)
class ReadLines(Operation):
    """Reads a file line by line."""

    def call(self, path: Path):
        """See class' docstring."""
        if path.filepath.is_dir():
            files = sorted([f for f in path.filepath.iterdir() if f.is_file()])
            for file in files:
                with file.open("r") as f:
                    for line in f:
                        path_str = line.strip()
                        yield Path(
                            filepath=epath.Path(path_str),
                            fullpath=pathlib.PurePath(path_str),
                        )
        else:
            with path.filepath.open("r") as f:
                for line in f:
                    path_str = line.strip()
                    yield Path(
                        filepath=epath.Path(path_str),
                        fullpath=pathlib.PurePath(path_str),
                    )
