"""Download operation module."""

import base64
import dataclasses
import hashlib
import logging
import os
import time
import urllib.parse

from etils import epath
import requests
import tqdm

from mlcroissant._src.core import constants
from mlcroissant._src.core.constants import EncodingFormat
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.core.optional import deps
from mlcroissant._src.core.path import get_fullpath
from mlcroissant._src.core.path import Path
from mlcroissant._src.core.url import is_url
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.structure_graph.nodes.file_object import FileObject

_CHUNK_SIZE = 1024
_GITHUB_GIT = "https://github.com"
_GITLAB_GIT = "https://gitlab.com"
_HUGGING_FACE_GIT = "https://huggingface.co/datasets"
_SUPPORTED_HOSTS = [
    _GITHUB_GIT,
    _GITLAB_GIT,
    _HUGGING_FACE_GIT,
]


def get_hash(url: str) -> str:
    """Retrieves the sha256 hash of an URL."""
    return hashlib.sha256(url.encode()).hexdigest()


def get_download_filepath(node: FileObject) -> epath.Path:
    """Retrieves the download filepath of an URL."""
    ctx = node.ctx
    if node.name in ctx.mapping:
        return ctx.mapping[node.name]
    url = node.content_url
    if url and not is_url(url) and not node.contained_in:
        if ctx.folder is None:
            raise ValueError(f"Could not find node folder={ctx.folder}")
        filepath = ctx.folder / url
        assert filepath.exists(), (
            f'In node "{node.uid}", file "{url}" is either an invalid URL'
            " or an invalid path."
        )
        # No need to download local files
        return filepath
    assert url, "Cannot get hashed URL for None."
    hashed_url = get_hash(url)
    constants.DOWNLOAD_PATH.mkdir(parents=True, exist_ok=True)
    return constants.DOWNLOAD_PATH / f"croissant-{hashed_url}"


def insert_credentials(url: str, username: str | None, password: str | None) -> str:
    """Inserts credentials in the URL for an HTTP authentication.

    Args:
        url: The Git URL.
        username: The username to use for the HTTPS authentication.
        password: The password to use for the HTTPS authentication.

    Returns:
        The URL populated with the given credentials. For example:
        `https://{username}:{password}@github.com/account/repo`.
    """
    https = "https://"
    if not url.startswith(https):
        raise ValueError("use secured HTTPS protocol for {url}.")
    if username is None and password is None:
        return url
    if username is None or password is None:
        raise ValueError(
            f"please provide both {constants.CROISSANT_GIT_USERNAME} and"
            f" {constants.CROISSANT_GIT_PASSWORD}."
        )
    username = urllib.parse.quote(username)
    password = urllib.parse.quote(password)
    https_with_credentials = f"{https}{username}:{password}@"
    return url.replace(https, https_with_credentials)


def extract_git_info(full_url: str) -> tuple[str, str | None]:
    """Extracts git-related information.

    Args:
        full_url: The full git URL for an HTTP clone.

    Returns:
        A tuple containing the base URL of the repository to clone and the refs to
        checkout if any is provided.
    """
    full_url = os.fspath(full_url)
    if full_url.startswith(_GITHUB_GIT) or full_url.startswith(_GITLAB_GIT):
        return full_url, None
    if full_url.startswith(_HUGGING_FACE_GIT):
        splits = full_url.rsplit("/tree/refs%2F", 1)
        if len(splits) == 1:
            # There is no refs in the URL: returning None.
            return splits[0], None
        else:
            url, refs = splits
            return url, f"refs/{urllib.parse.unquote(refs)}"
    else:
        raise ValueError(
            f"unknown git host: {full_url}. Supported git hosts:"
            f" {_SUPPORTED_HOSTS}. Contact the Croissant team to support more hosts."
        )


def _get_hash_algorithm(file_object: FileObject):
    if file_object.md5:
        return hashlib.md5()
    elif file_object.sha256:
        return hashlib.sha256()
    else:
        raise ValueError("md5 and sha256 are not specified.")


def get_basic_auth_from_env() -> tuple[str, str] | None:
    """Determines a Basic Auth tuple from the environment variables.

    This method determines the username and password for the auth tuple from the
    `CROISSANT_BASIC_AUTH_USERNAME` and `CROISSANT_BASIC_AUTH_PASSWORD` env variables.

    Returns:
        The Basic Auth tuple if the env variables are configured properly. Otherwise, it
        returns None.
    """
    username = os.environ.get(constants.CROISSANT_BASIC_AUTH_USERNAME)
    password = os.environ.get(constants.CROISSANT_BASIC_AUTH_PASSWORD)
    return None if username is None or password is None else (username, password)


@dataclasses.dataclass(frozen=True, repr=False)
class Download(Operation):
    """Downloads from a URL to the disk."""

    node: FileObject

    def _check_hash(self, filepath: epath.Path):
        if filepath.is_dir():
            return
        hash = _get_hash_algorithm(self.node)
        with filepath.open("rb") as f:
            while chunk := f.read(_CHUNK_SIZE):
                hash.update(chunk)
        # The hash from the Croissant JSON-LD can be in either hex or base64,
        # so let's check both
        expected_hash = getattr(self.node, hash.name)
        # First, try hex as that's likely more common
        hex_hash = hash.hexdigest()
        if hex_hash == expected_hash:
            return
        # Next, try base64 as a fallback
        base64_hash = base64.b64encode(bytes.fromhex(hex_hash)).decode()
        if base64_hash == expected_hash:
            return

        logging.info(
            "Hash of downloaded file is not identical with reference in metadata.json"
        )
        # In v0.8 only, hashes were not checked.
        ctx = self.node.ctx
        if ctx.conforms_to and ctx.conforms_to > CroissantVersion.V_0_8:
            raise ValueError(
                f"Hash of downloaded file {filepath} is not identical with the"
                f" reference in the Croissant JSON-LD. Expected: {expected_hash} -"
                f" Got: {hex_hash} (hex) / {base64_hash} (base64)"
            )

    def _download_from_http(self, filepath: epath.Path):
        content_url = self.node.content_url
        assert content_url, "Content URL is None."
        response = requests.get(
            content_url, stream=True, timeout=10, auth=get_basic_auth_from_env()
        )
        response.raise_for_status()
        total = int(response.headers.get("Content-Length", 0))
        with filepath.open("wb") as file, tqdm.tqdm(
            desc=f"Downloading {content_url}...",
            total=total,
            unit="iB",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=_CHUNK_SIZE):
                size = file.write(data)
                bar.update(size)

    def _download_from_git(self, filepath: epath.Path):
        username = os.environ.get(constants.CROISSANT_GIT_USERNAME)
        password = os.environ.get(constants.CROISSANT_GIT_PASSWORD)
        # GIT_LFS_SKIP_SMUDGE allows to not download git-lfs files by default. Those
        # files may be big, so we want to download them just-in-time (see `Read`):
        os.environ["GIT_LFS_SKIP_SMUDGE"] = "1"

        assert self.node.content_url, "Cannot extract git-related information for None."
        url, refs = extract_git_info(self.node.content_url)
        url = insert_credentials(url, username, password)
        repo = deps.git.Repo.clone_from(url, filepath)
        # Hugging Face uses https://git-scm.com/book/en/v2/Git-Internals-Git-References.
        if refs:
            branch_name = f"branch_{time.time()}"  # Branch name with no conflict
            repo.remote().fetch(f"{refs}:{branch_name}")
            repo.branches[branch_name].checkout()

    def __call__(self, *args) -> Path:
        """See class' docstring."""
        del args  # unused
        filepath = get_download_filepath(self.node)
        if not filepath.exists():
            if self.node.encoding_format == EncodingFormat.GIT:
                self._download_from_git(filepath)
            else:
                self._download_from_http(filepath)
        self._check_hash(filepath)
        logging.info(
            "File %s is downloaded to %s", self.node.content_url, os.fspath(filepath)
        )
        return Path(
            filepath=filepath,
            fullpath=get_fullpath(filepath, constants.DOWNLOAD_PATH),
        )
