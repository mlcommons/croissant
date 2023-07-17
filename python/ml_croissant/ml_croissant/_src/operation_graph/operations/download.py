"""Download operation module."""

import concurrent.futures
import dataclasses
import hashlib
import logging
import os

from etils import epath
from ml_croissant._src.core.constants import DOWNLOAD_PATH
from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.operation_graph.base_operation import Operation
import networkx as nx
import requests
import tqdm

_DOWNLOAD_CHUNK_SIZE = 1024


def is_url(url: str) -> bool:
    """Tests whether a URL is valid.

    The current version is very loose and only supports the HTTP protocol.
    """
    return url.startswith("http://") or url.startswith("https://")


def get_hash(url: str) -> str:
    """Retrieves the sha256 hash of an URL."""
    return hashlib.sha256(url.encode()).hexdigest()


def get_download_filepath(node: Node, url: str) -> epath.Path:
    """Retrieves the download filepath of an URL."""
    if not is_url(url):
        assert url.startswith("data/"), (
            'Local file "{self.node.uid}" should point to a file within the data/'
            ' folder next to the JSON-LD Croissant file. But got: "{self.url}"'
        )
        filepath = node.folder / url
        assert filepath.exists(), (
            f'In node "{node.uid}", file "{url}" is either an invalid URL'
            " or an invalid path."
        )
        # No need to download local files
        return filepath
    hashed_url = get_hash(url)
    DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
    return DOWNLOAD_PATH / f"croissant-{hashed_url}"


@dataclasses.dataclass(frozen=True, repr=False)
class Download(Operation):
    """Downloads from a URL to the disk."""

    url: str

    def __call__(self):
        """See class' docstring."""
        filepath = get_download_filepath(self.node, self.url)
        if not filepath.exists():
            response = requests.get(self.url, stream=True, timeout=10)
            total = int(response.headers.get("Content-Length", 0))
            with filepath.open("wb") as file, tqdm.tqdm(
                desc=f"Downloading {self.url}...",
                total=total,
                unit="iB",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(chunk_size=_DOWNLOAD_CHUNK_SIZE):
                    size = file.write(data)
                    bar.update(size)
        logging.info("File %s is downloaded to %s", self.url, os.fspath(filepath))


def execute_downloads(operations: nx.MultiDiGraph):
    """Executes all the downloads in the graph of operations."""
    downloads = [
        operation for operation in operations.nodes if isinstance(operation, Download)
    ]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for download in downloads:
            executor.submit(download)
