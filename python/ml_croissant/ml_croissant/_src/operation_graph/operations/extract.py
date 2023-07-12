"""Extract operation module."""

import dataclasses
import fnmatch
import logging
import os
import re
import tarfile

from etils import epath
from ml_croissant._src.core.constants import EXTRACT_PATH
from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.operation_graph.operations.download import (
    get_download_filepath,
    get_hash,
)
from ml_croissant._src.structure_graph.nodes import FileObject, FileSet
import pandas as pd


@dataclasses.dataclass(frozen=True, repr=False)
class Untar(Operation):
    """Un-tars "application/x-tar" and yields filtered lines."""

    node: FileObject
    target_node: FileSet

    def __call__(self):
        includes = fnmatch.translate(self.target_node.includes)
        url = self.node.content_url
        archive_file = get_download_filepath(self.node, url)
        hashed_url = get_hash(url)
        extract_dir = EXTRACT_PATH / hashed_url
        if not extract_dir.exists():
            with tarfile.open(archive_file) as tar:
                tar.extractall(extract_dir)
        logging.info(
            "Found directory where data is extracted: %s.", os.fspath(extract_dir)
        )
        included_files = []
        for basepath, _, files in os.walk(extract_dir):
            for file in files:
                if re.match(includes, os.fspath(file)):
                    included_files.append(epath.Path(basepath) / file)
        return pd.DataFrame(
            {
                "filepath": included_files,
                "filename": [file.name for file in included_files],
            }
        )
