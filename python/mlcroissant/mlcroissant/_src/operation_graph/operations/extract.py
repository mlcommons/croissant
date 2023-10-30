"""Extract operation module."""

import dataclasses
import logging
import os
import tarfile
import zipfile

from etils import epath

from mlcroissant._src.core.constants import EncodingFormat
from mlcroissant._src.core.constants import EXTRACT_PATH
from mlcroissant._src.core.path import get_fullpath
from mlcroissant._src.core.path import Path
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.operation_graph.operations.download import get_hash
from mlcroissant._src.structure_graph.nodes.file_object import FileObject


def should_extract(encoding_format: str | None) -> bool:
    """Whether the encoding format should be extracted (zip or tar)."""
    return (
        encoding_format == EncodingFormat.TAR or encoding_format == EncodingFormat.ZIP
    )


def _extract_file(source: epath.Path, target: epath.Path) -> None:
    """Extracts the `source` file to `target`."""
    if zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as zip:
            zip.extractall(target)
    elif tarfile.is_tarfile(source):
        with tarfile.open(source) as tar:
            tar.extractall(target)
    else:
        raise ValueError(f"Unsupported compression method for file: {source}")


@dataclasses.dataclass(frozen=True, repr=False)
class Extract(Operation):
    """Extracts tar/zip and yields the extract Path."""

    node: FileObject

    def __call__(self, archive_file: Path) -> Path:
        """See class' docstring."""
        url = self.node.content_url
        assert url, "Content of URL for this node is None"
        hashed_url = get_hash(url)
        extract_dir = EXTRACT_PATH / hashed_url
        if not extract_dir.exists():
            _extract_file(archive_file.filepath, extract_dir)
        logging.info(
            "Found directory where data is extracted: %s", os.fspath(extract_dir)
        )
        return Path(
            filepath=extract_dir,
            fullpath=get_fullpath(extract_dir, EXTRACT_PATH),
        )
