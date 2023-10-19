"""Read operation module."""

import dataclasses
import json

from etils import epath
import pandas as pd

from mlcroissant._src.core.git import download_git_lfs_file
from mlcroissant._src.core.git import is_git_lfs_file
from mlcroissant._src.core.path import Path
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.operation_graph.operations.download import is_url
from mlcroissant._src.operation_graph.operations.parse_json import parse_json_content
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.file_object import FileObject
from mlcroissant._src.structure_graph.nodes.file_set import FileSet
from mlcroissant._src.structure_graph.nodes.source import FileProperty


@dataclasses.dataclass(frozen=True, repr=False)
class Read(Operation):
    """Reads from a file and output a pd.DataFrame."""

    node: FileObject | FileSet
    folder: epath.Path
    fields: tuple[Field, ...]

    def _read_file_content(self, encoding_format: str, file: Path) -> pd.DataFrame:
        """Extracts the `source` file to `target`."""
        filepath = file.filepath
        if is_git_lfs_file(filepath):
            download_git_lfs_file(file)
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
            elif encoding_format == "application/jsonlines":
                return pd.read_json(file, lines=True)
            elif encoding_format == "application/x-parquet":
                try:
                    return pd.read_parquet(file)
                except ImportError as e:
                    raise ImportError(
                        "Missing dependency to read Parquet files. pyarrow is not"
                        " installed. Please, install `pip install"
                        " mlcroissant[parquet]`."
                    ) from e
            elif encoding_format == "text/plain":
                return pd.DataFrame(
                    {
                        FileProperty.content: [file.read()],
                    }
                )
            else:
                raise ValueError(
                    f"Unsupported encoding format for file: {encoding_format}"
                )

    def __call__(self, files: list[Path] | Path) -> pd.DataFrame:
        """See class' docstring."""
        if isinstance(files, Path):
            files = [files]
        file_contents = []
        for file in files:
            # The FileObject is extracted from another FileObject/FileSet:
            if isinstance(self.node, FileObject) and self.node.contained_in:
                content_url = self.node.content_url
                file = Path(
                    filepath=file.filepath / content_url,
                    fullpath=file.fullpath / content_url,
                )
            # The FileObject comes from disk:
            elif isinstance(self.node, FileObject) and not is_url(
                self.node.content_url
            ):
                # Read from the local path
                assert file.filepath.exists(), (
                    f'In node "{self.node.uid}", file "{self.node.content_url}" is'
                    " either an invalid URL or an invalid path."
                )
            file_content = self._read_file_content(self.node.encoding_format, file)
            file_content[FileProperty.filepath] = file.filepath
            file_content[FileProperty.filename] = file.filename
            file_content[FileProperty.fullpath] = file.fullpath
            file_contents.append(file_content)
        return pd.concat(file_contents)
