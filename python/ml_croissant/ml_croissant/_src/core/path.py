"""Core utils to manipulate paths."""

import dataclasses
import os
import pathlib

from etils import epath


@dataclasses.dataclass
class Path:
    """Container class for paths in Croissant.

    Args:
        filepath: The full file path on disk.
        fullpath: `fullpath` in the sense of Croissant, i.e. the full path relative to
            the Croissant folders. This field may sound wrongly named, but it is named
            after the same JSON-LD field (see `fileProperty` in the Croissant specs).
            Example: for filepath=`${CROISSANT_CACHE}/downloads/my-dataset/my-file`, the
            fullpath is `my-dataset/my-file`.
    """

    filepath: epath.Path
    fullpath: pathlib.PurePath

    def __lt__(self, other):
        """Implements < for File allowing to sort a list[File]."""
        return os.fspath(self.filepath) < os.fspath(other.filepath)

    @property
    def filename(self) -> str:
        """The name of the file if it is a file."""
        return self.filepath.name


def get_fullpath(file: epath.Path, data_dir: epath.Path) -> pathlib.PurePath:
    """Returns the relative path relatively to `data_dir`."""
    # Path since the root of the dir.
    fullpath = os.fspath(file).replace(os.fspath(data_dir), "")
    # Remove the trailing slash.
    if fullpath.startswith("/"):
        fullpath = fullpath[1:]
    return pathlib.PurePath(fullpath)


def get_fullpaths(
    files: list[epath.Path], data_dir: epath.Path
) -> list[pathlib.PurePath]:
    """Returns the relative paths relatively to `data_dir`."""
    return [get_fullpath(file, data_dir) for file in files]
