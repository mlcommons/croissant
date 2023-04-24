import dataclasses
import json
from typing import Union

from absl import logging
from etils import epath

from format.src import errors
from format.src import graphs

FileOrFilePath = Union[str, epath.PathLike, dict]


def _load_file(file: FileOrFilePath) -> dict:
    if isinstance(file, str):
        file = epath.Path(file)
        if not file.exists():
            raise ValueError(f"File {file} does not exist.")
    if isinstance(file, epath.PathLike):
        with file.open() as file:
            file = json.load(file)
    if not isinstance(file, dict):
        raise ValueError("The file is not a valid JSON-LD, because it's not an object.")
    return file


@dataclasses.dataclass
class Validator:
    file_or_file_path: FileOrFilePath
    issues: errors.Issues = dataclasses.field(default_factory=errors.Issues)
    file: dict = dataclasses.field(init=False)

    def run(self):
        try:
            self.file = _load_file(self.file_or_file_path)
            self.graph = graphs.load_rdf_graph(self.file)
            graphs.check_graph(self.issues, self.graph)
        except Exception as exception:
            if self.issues.errors:
                raise errors.ValidationError(self.issues.report()) from exception
            raise exception
        if self.issues.errors:
            raise errors.ValidationError(self.issues.report())
        elif self.issues.warnings:
            logging.warning(self.issues.report())


@dataclasses.dataclass
class Dataset:
    file: FileOrFilePath

    def __post_init__(self):
        self.validator = Validator(self.file)
        self.validator.run()
        self.file = self.validator.file
