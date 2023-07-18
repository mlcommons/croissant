"""Read operation module."""

import dataclasses

from etils import epath
from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.operation_graph.operations.download import (
    is_url,
    get_download_filepath,
)
import pandas as pd


@dataclasses.dataclass(frozen=True, repr=False)
class ReadCsv(Operation):
    """Reads from a CSV file and yield lines."""

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
        with filepath.open("rb") as csvfile:
            return pd.read_csv(csvfile)
