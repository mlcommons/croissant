"""Read operation module."""

import dataclasses
import json

from etils import epath
from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.structure_graph.nodes import FileObject
from ml_croissant._src.operation_graph.operations.download import (
    is_url,
    get_download_filepath,
)
import pandas as pd


def _read_file(encoding_format: str, filepath: epath.Path) -> None:
    """Extracts the `source` file to `target`."""
    with filepath.open("rb") as file:
        if encoding_format == "text/csv":
            return pd.read_csv(file)
        elif encoding_format == "application/json":
            return json.load(file)
        else:
            raise ValueError(f"Unsupported encoding format for file: {encoding_format}")


@dataclasses.dataclass(frozen=True, repr=False)
class Read(Operation):
    """Reads from a CSV file and yield lines."""

    node: FileObject
    url: str
    folder: epath.Path

    def __call__(self):
        """See class' docstring."""
        if is_url(self.url):
            filepath = get_download_filepath(self.node, self.url)
        else:
            # Read from the local path
            filepath = self.folder / self.url
            assert filepath.exists(), (
                f'In node "{self.node.uid}", file "{self.url}" is either an invalid URL'
                " or an invalid path."
            )
        return _read_file(self.node.encoding_format, filepath)
