"""datasets module."""

import dataclasses
import json
from typing import Union

from absl import logging
from etils import epath

from format.src import computations
from format.src import errors
from format.src import graphs

FileOrFilePath = Union[str, epath.PathLike, dict]


def _load_file(file: FileOrFilePath) -> dict:
    if isinstance(file, str):
        file = epath.Path(file)
        if not file.exists():
            raise ValueError(f"File {file} does not exist.")
    if isinstance(file, epath.PathLike):
        with file.open() as filedescriptor:
            file = json.load(filedescriptor)
    if not isinstance(file, dict):
        raise ValueError("The file is not a valid JSON-LD, because it's not an object.")
    return file


@dataclasses.dataclass
class Validator:
    """Static analysis of the issues in the Croissant file."""

    file_or_file_path: FileOrFilePath
    issues: errors.Issues = dataclasses.field(default_factory=errors.Issues)
    file: dict = dataclasses.field(init=False)

    def run(self):
        try:
            self.file = _load_file(self.file_or_file_path)
            rdf_graph = graphs.load_rdf_graph(self.file)
            nodes = graphs.check_rdf_graph(self.issues, rdf_graph)

            entry_node, structure_graph = computations.build_structure_graph(
                self.issues, nodes
            )
            # Feature toggling: do not check for MovieLens, because we need more features.
            if entry_node.uid == "Movielens-25M":
                return
            self.operations = computations.ComputationGraph.from_nodes(
                self.issues, entry_node, structure_graph
            )
            self.operations.check_graph()
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
        self.operations = self.validator.operations

    def generate(self):
        """Executes all operations to generate the dataset."""
        print('Graph of operations:', self.operations)
