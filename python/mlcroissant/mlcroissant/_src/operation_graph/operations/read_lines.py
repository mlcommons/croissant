"""ReadLines operation module."""

import dataclasses

from etils import epath

from mlcroissant._src.core.path import Path
from mlcroissant._src.operation_graph.base_operation import Operation


@dataclasses.dataclass(frozen=True, repr=False)
class ReadLines(Operation):
    """Reads a file line by line."""

    def call(self, path: Path):
        """See class' docstring."""
        if path.filepath.is_dir():
            files = list(path.filepath.glob("*"))
            if len(files) != 1:
                raise ValueError(
                    f"ReadLines expects a single file, but found {len(files)} files in"
                    f" {path.filepath}"
                )
            path = Path(filepath=files[0], fullpath=path.fullpath)
        with path.filepath.open("r") as f:
            for line in f:
                line = line.strip()
                yield Path(
                    filepath=path.filepath / line,
                    fullpath=epath.Path(line),
                )
