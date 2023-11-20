"""Tests for git."""

import pathlib
import tempfile
from unittest import mock

from etils import epath

from mlcroissant._src.core.git import download_git_lfs_file
from mlcroissant._src.core.git import is_git_lfs_file
from mlcroissant._src.core.optional import deps
from mlcroissant._src.core.path import Path

_GIT_LFS_CONTENT = lambda: """version https://git-lfs.github.com/spec/v1
oid sha256:5e2785fcd9098567a49d6e62e328923d955b307b6dcd0492f6234e96e670772a
size 309207547
"""

_NON_GIT_LFS_CONTENT = lambda: """name,age
a,1
b,2
c,3"""

_NON_ASCII_CONTENT = lambda: (255).to_bytes(1, byteorder="big")


def test_is_git_lfs_file():
    with tempfile.TemporaryDirectory() as tempdir:
        tempdir = epath.Path(tempdir)

        gitlfs_file = tempdir / "gitlfs"
        gitlfs_file.write_text(_GIT_LFS_CONTENT())
        assert is_git_lfs_file(gitlfs_file)

        no_gitlfs_file = tempdir / "no-gitlfs"
        no_gitlfs_file.write_text(_NON_GIT_LFS_CONTENT())
        assert not is_git_lfs_file(no_gitlfs_file)

        no_ascii_file = tempdir / "no-ascii"
        no_ascii_file.write_bytes(_NON_ASCII_CONTENT())
        assert not is_git_lfs_file(no_ascii_file)


def test_download_git_lfs_file():
    file = Path(
        filepath=epath.Path("/tmp/full/path.json"),
        fullpath=pathlib.PurePath("path.json"),
    )
    git = deps.git
    with mock.patch.object(git, "Git", autospec=True) as git_mock:
        download_git_lfs_file(file)
        git_mock.assert_called_once_with("/tmp/full/")
        git_mock.return_value.execute.assert_called_once_with([
            "git", "lfs", "pull", "--include", "path.json"
        ])
