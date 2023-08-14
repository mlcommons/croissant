"""Read operation module."""

import dataclasses
import json

from etils import epath
from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.structure_graph.nodes import Field, FileObject, FileProperty
from ml_croissant._src.operation_graph.operations.download import (
    is_url,
    get_download_filepath,
)
from ml_croissant._src.operation_graph.operations.parse_json import parse_json_content
import pandas as pd


@dataclasses.dataclass(frozen=True, repr=False)
class Read(Operation):
    """Reads from a CSV file and yield lines."""

    node: FileObject
    url: str
    folder: epath.Path
    fields: list[Field]

    def _read_file_content(
        self, encoding_format: str, filepath: epath.Path
    ) -> pd.DataFrame:
        """Extracts the `source` file to `target`."""
        with filepath.open("rb") as file:
            if encoding_format == "text/csv":
                return pd.read_csv(file)
            elif encoding_format == "application/json":
                json_content = json.load(file)
                fields = list(self.fields)
                has_parse_json = any(field.source.extract.json_path for field in fields)
                if has_parse_json:
                    return parse_json_content(json_content, fields)
                # Raw files are returned as a one-line pd.DataFrame.
                return pd.DataFrame(
                    {
                        FileProperty.content: [json_content],
                    }
                )
            else:
                raise ValueError(
                    f"Unsupported encoding format for file: {encoding_format}"
                )

    def __call__(self) -> tuple[str, pd.DataFrame]:
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
        file_content = self._read_file_content(self.node.encoding_format, filepath)
        file_content[FileProperty.filepath] = filepath
        file_content[FileProperty.filename] = filepath.name
        file_content[FileProperty.fullpath] = filepath
        return file_content
