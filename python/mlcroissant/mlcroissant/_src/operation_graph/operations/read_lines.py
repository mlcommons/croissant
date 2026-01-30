"""ReadLines operation module."""

import dataclasses

from etils import epath

from mlcroissant._src.core.path import Path
from mlcroissant._src.operation_graph.base_operation import Operation


@dataclasses.dataclass(frozen=True, repr=False)
class ReadLines(Operation):
    """Reads a file line by line and returns Path objects."""

    def call(self, path: Path):
        """See class' docstring."""
        filepath = path.filepath
        if filepath.is_dir():
            files = list(filepath.glob("*"))
            # We expect exactly one file inside to avoid ambiguity about which file to
            # read.
            if len(files) != 1:
                raise ValueError(
                    f"ReadLines expects a single file, but found {len(files)} files in"
                    f" {filepath}"
                )
            filepath = files[0]
        with filepath.open("r") as f:
            for line in f:
                line = line.strip()
                yield Path(
                    filepath=filepath / line,
                    fullpath=epath.Path(line),
                )
