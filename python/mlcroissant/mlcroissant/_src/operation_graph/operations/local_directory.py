"""LocalDirectory operation module."""

import dataclasses

from etils import epath

from mlcroissant._src.core.path import Path
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.structure_graph.nodes.file_set import FileSet


@dataclasses.dataclass(frozen=True, repr=False)
class LocalDirectory(Operation):
    """Defines a local directory to read files from."""

    node: FileSet
    folder: epath.Path

    def __call__(self, *args):
        """See class' docstring."""
        del args
        return Path(
            filepath=self.folder,
            fullpath=self.folder,
        )
