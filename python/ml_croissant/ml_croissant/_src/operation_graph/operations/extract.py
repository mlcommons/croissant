"""Extract operation module."""

import dataclasses
import fnmatch
import logging
import os
import re
import tarfile
import zipfile

from etils import epath
import pandas as pd

from ml_croissant._src.core.constants import EXTRACT_PATH
from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.operation_graph.operations.download import get_download_filepath
from ml_croissant._src.operation_graph.operations.download import get_hash
from ml_croissant._src.structure_graph.nodes import FileObject
from ml_croissant._src.structure_graph.nodes import FileProperty
from ml_croissant._src.structure_graph.nodes import FileSet


def should_extract(encoding_format: str) -> bool:
    """Whether the encoding format should be extracted (zip or tar)."""
    return (
        encoding_format == "application/x-tar" or encoding_format == "application/zip"
    )


def get_fullpath(file: epath.Path, data_dir: epath.Path) -> str:
    """Fullpaths are the full paths from the extraction directory."""
    # Path since the root of the dir.
    fullpath = os.fspath(file).replace(os.fspath(data_dir), "")
    # Remove the trailing slash.
    if fullpath.startswith("/"):
        fullpath = fullpath[1:]
    return fullpath


def _get_fullpaths(files: list[epath.Path], extract_dir: epath.Path) -> list[str]:
    """Fullpaths are the full paths from the extraction directory."""
    return [get_fullpath(file, extract_dir) for file in files]


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
    """Extracts tar/zip and yields filtered pd.DataFrame."""

    node: FileObject
    target_node: FileSet

    def __call__(self):
        """See class' docstring."""
        includes = fnmatch.translate(self.target_node.includes)
        url = self.node.content_url
        archive_file = get_download_filepath(self.node, url)
        hashed_url = get_hash(url)
        extract_dir = EXTRACT_PATH / hashed_url
        if not extract_dir.exists():
            _extract_file(archive_file, extract_dir)
        logging.info(
            "Found directory where data is extracted: %s", os.fspath(extract_dir)
        )
        included_files = []
        for basepath, _, files in os.walk(extract_dir):
            for file in files:
                if re.match(includes, os.fspath(file)):
                    included_files.append(epath.Path(basepath) / file)
        # We need to sort `files` to have a deterministic/reproducible order.
        included_files.sort()
        return pd.DataFrame(
            {
                FileProperty.filepath: included_files,
                FileProperty.filename: [file.name for file in included_files],
                FileProperty.fullpath: _get_fullpaths(included_files, extract_dir),
            }
        )
