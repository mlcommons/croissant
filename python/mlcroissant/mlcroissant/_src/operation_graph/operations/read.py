"""Read operation module."""

import dataclasses
import enum
import json

from etils import epath
import pandas as pd

from mlcroissant._src.core.constants import EncodingFormat
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


class ReadingMethod(enum.Enum):
    """Reading method derived from the fields that consume the FileObject/FileSet."""

    CONTENT = enum.auto()
    JSON = enum.auto()
    LINES = enum.auto()
    NONE = enum.auto()


def _reading_method(
    node: FileObject | FileSet, fields: tuple[Field, ...]
) -> ReadingMethod:
    """Extracts the reading method from the fields.

    If several reading methods are found, we raise an error for now. Indeed, it is
    unlikely that the same FileObject/FileSet has to be read in different manners. Also,
    an alternative solution is to define n FileObjects/FileSets when you have n
    different reading methods.
    """
    reading_methods: set[ReadingMethod] = set()
    for field in fields:
        extract = field.source.extract
        if extract.column:
            reading_methods.add(ReadingMethod.CONTENT)
        elif extract.file_property == FileProperty.lines:
            reading_methods.add(ReadingMethod.LINES)
        elif extract.file_property == FileProperty.content:
            reading_methods.add(ReadingMethod.CONTENT)
        elif extract.json_path:
            reading_methods.add(ReadingMethod.JSON)
    if len(reading_methods) == 0:
        return ReadingMethod.NONE
    if len(reading_methods) > 1:
        raise ValueError(
            f"Cannot read {node=}. The fields use several reading methods:"
            f" {reading_methods}. Reading the same FileObject/FileSet using different"
            " reading methods has yet to be implemented. Please, create an issue"
            " (https://github.com/mlcommons/croissant/issues/new) if your dataset"
            " requires this feature. Alternatively, you can use two different"
            " FileObject/FileSet pointing to the same resource."
        )
    return next(iter(reading_methods))


def _should_append_line_numbers(fields: tuple[Field, ...]) -> bool:
    """Checks whether at least one field requires listing the line numbers."""
    for field in fields:
        if field.source.extract.file_property == FileProperty.lineNumbers:
            return True
    return False


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
        reading_method = _reading_method(self.node, self.fields)
        with filepath.open("rb") as file:
            if encoding_format == EncodingFormat.CSV:
                return pd.read_csv(file)
            elif encoding_format == EncodingFormat.TSV:
                return pd.read_csv(file, sep="\t")
            elif encoding_format == EncodingFormat.JSON:
                json_content = json.load(file)
                if reading_method == ReadingMethod.JSON:
                    return parse_json_content(json_content, self.fields)
                else:
                    # Raw files are returned as a one-line pd.DataFrame.
                    return pd.DataFrame({
                        FileProperty.content: [json_content],
                    })
            elif encoding_format == EncodingFormat.JSON_LINES:
                return pd.read_json(file, lines=True)
            elif encoding_format == EncodingFormat.PARQUET:
                try:
                    return pd.read_parquet(file)
                except ImportError as e:
                    raise ImportError(
                        "Missing dependency to read Parquet files. pyarrow is not"
                        " installed. Please, install `pip install"
                        " mlcroissant[parquet]`."
                    ) from e
            elif encoding_format == EncodingFormat.TEXT:
                if reading_method == ReadingMethod.LINES:
                    return pd.read_csv(
                        filepath, header=None, names=[FileProperty.lines]
                    )
                else:
                    return pd.DataFrame({
                        FileProperty.content: [file.read()],
                    })
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
            if (
                isinstance(self.node, FileObject)
                and self.node.content_url
                and self.node.contained_in
            ):
                content_url = self.node.content_url
                file = Path(
                    filepath=file.filepath / content_url,
                    fullpath=file.fullpath / content_url,
                )
            # The FileObject comes from disk:
            elif (
                isinstance(self.node, FileObject)
                and self.node.content_url
                and not is_url(self.node.content_url)
            ):
                # Read from the local path
                assert file.filepath.exists(), (
                    f'In node "{self.node.uid}", file "{self.node.content_url}" is'
                    " either an invalid URL or an invalid path."
                )
            assert self.node.encoding_format, "Encoding format is not specified."
            file_content = self._read_file_content(self.node.encoding_format, file)
            if _should_append_line_numbers(self.fields):
                file_content[FileProperty.lineNumbers] = range(len(file_content))
            file_content[FileProperty.filepath] = file.filepath
            file_content[FileProperty.filename] = file.filename
            file_content[FileProperty.fullpath] = file.fullpath
            file_contents.append(file_content)
        return pd.concat(file_contents)
