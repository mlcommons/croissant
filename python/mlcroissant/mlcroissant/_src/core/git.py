"""git module."""

import os

from absl import logging
from etils import epath

from mlcroissant._src.core.optional import deps
from mlcroissant._src.core.path import Path


def is_git_lfs_file(filepath: epath.Path) -> bool:
    """Returns whether a file a non-downloaded git-lfs file by checking its header.

    An optimization of this function would be to only read the file if there is a git
    repository in the distribution.
    """
    with open(filepath, "rb") as file:
        # Only read the first line of the file. In the future, this could be a problem,
        # e.g. if we accept *.txt files and the file starts with the same header.
        first_line = file.readline()
        if first_line.startswith(b"version https://git-lfs.github.com/spec"):
            return True
    return False


def download_git_lfs_file(file: Path):
    """Downloads a specific git-lfs file within its repo."""
    # Path(filepath="/tmp/full/path.json", fullpath="path.json")
    # => working_dir = "/tmp/full"
    fullpath = os.fspath(file.fullpath)
    working_dir = os.fspath(file.filepath).rsplit(fullpath)[0]
    repo = deps.git.Git(working_dir)
    logging.info(
        "Downloading git-lfs file: %s in working dir: %s", fullpath, working_dir
    )
    try:
        repo.execute(["git", "lfs", "pull", "--include", fullpath])
    except deps.git.exc.GitCommandError as ex:
        raise RuntimeError(
            "Problem when launching `git lfs`. "
            "Possible problems: Have you installed git lfs "
            f"locally? Is '{fullpath}' a valid `git lfs` "
            "repository?"
        ) from ex
