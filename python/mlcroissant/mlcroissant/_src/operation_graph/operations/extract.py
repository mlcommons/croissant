"""Extract operation module."""

import dataclasses
import gzip
import logging
import os
import shutil
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


def should_extract(encoding_formats: list[str] | None) -> bool:
    """Whether the encoding format should be extracted (zip or tar)."""
    if not encoding_formats:
        return False
    return (
        EncodingFormat.TAR in encoding_formats or EncodingFormat.ZIP in encoding_formats
    )


def is_gzip(file: epath.Path) -> bool:
    """Whether the given file is GZIP compressed by examining its magic number."""
    with file.open("rb") as f:
        return f.read(2) == b"\x1f\x8b"


def _extract_file(source: epath.Path, target: epath.Path) -> None:
    """Extracts the `source` file to `target`."""
    if zipfile.is_zipfile(source):
        with zipfile.ZipFile(source) as zip:
            zip.extractall(target)
    elif tarfile.is_tarfile(source):
        with tarfile.open(source) as tar:
            tar.extractall(target)
    elif is_gzip(source):
        target.mkdir(parents=True, exist_ok=True)
        with gzip.open(source, "rb") as f_in:
            with open(target / source.stem, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
    else:
        raise ValueError(f"Unsupported compression method for file: {source}")


@dataclasses.dataclass(frozen=True, repr=False)
class Extract(Operation):
    """Extracts tar/zip and yields the extract Path."""

    node: FileObject

    def call(self, archive_file: Path) -> Path:
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
