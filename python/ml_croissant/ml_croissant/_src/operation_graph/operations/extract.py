"""Extract operation module."""

import dataclasses
import fnmatch
import logging
import os
import re
import tarfile
import zipfile

from etils import epath
from ml_croissant._src.core.constants import EXTRACT_PATH
from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.operation_graph.operations.download import (
    get_download_filepath,
    get_hash,
)
from ml_croissant._src.structure_graph.nodes import FileObject, FileSet
import pandas as pd


def should_extract(encoding_format: str) -> bool:
    """Whether the encoding format should be extracted (zip or tar)."""
    return (
        encoding_format == "application/x-tar" or encoding_format == "application/zip"
    )


def _get_fullpaths(files: list[epath.Path], extract_dir: epath.Path) -> list[str]:
    """Fullpaths are the full paths from the extraction directory."""
    fullpaths = []
    for file in files:
        # Path since the root of the extraction dir.
        root_path = os.fspath(file).replace(os.fspath(extract_dir), "")
        # Remove the trailing slash.
        if root_path.startswith("/"):
            root_path = root_path[1:]
        fullpaths.append(root_path)
    return fullpaths


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
                "filepath": included_files,
                "filename": [file.name for file in included_files],
                "fullpath": _get_fullpaths(included_files, extract_dir),
            }
        )
