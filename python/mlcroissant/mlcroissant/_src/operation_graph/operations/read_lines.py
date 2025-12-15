"""ReadLines operation module."""

import dataclasses

from mlcroissant._src.core.path import Path
from mlcroissant._src.operation_graph.base_operation import Operation


@dataclasses.dataclass(frozen=True, repr=False)
class ReadLines(Operation):
    """Reads a file line by line."""

    def call(self, path: Path):
        """See class' docstring."""
        with path.filepath.open("r") as f:
            for line in f:
                yield line.strip()
