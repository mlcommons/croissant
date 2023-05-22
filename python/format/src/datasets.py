"""datasets module."""

import dataclasses
import json
from typing import Union

from absl import logging
from etils import epath
from format.src import errors
from format.src import graphs
from format.src.computations import (
    build_structure_graph,
    ComputationGraph,
    get_entry_nodes,
    Operation,
)
import networkx as nx
import pandas as pd

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
    operations: ComputationGraph | None = None

    def run_static_analysis(self):
        try:
            self.file = _load_file(self.file_or_file_path)
            rdf_graph = graphs.load_rdf_graph(self.file)
            nodes = graphs.check_rdf_graph(self.issues, rdf_graph)

            entry_node, structure_graph = build_structure_graph(self.issues, nodes)
            # Feature toggling: do not check for MovieLens, because we need more
            # features.
            if entry_node.uid == "Movielens-25M":
                return
            self.operations = ComputationGraph.from_nodes(
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
    """Iterable dataset.

    Args:
        file: A JSON object or a path to a Croissant file (string or pathlib.Path).
    """

    file: FileOrFilePath
    operations: ComputationGraph | None = None

    def __post_init__(self):
        """Runs the static analysis of `file`."""
        self.validator = Validator(self.file)
        self.validator.run_static_analysis()
        self.file = self.validator.file
        self.operations = self.validator.operations

    def __iter__(self):
        """Executes all operations, runs dynamic analysis and yields examples."""
        entry_nodes = get_entry_nodes(self.operations.graph)
        visited = set()
        operations = self.list_operations(
            start=entry_nodes[0], visited=visited, skip_visited=False
        )
        for operation in operations:
            logging.info('Executing "%s"', operation)
            result = operation()
            visited.add(operation)
            if isinstance(result, pd.DataFrame):
                for _, line in result.iterrows():
                    line_operations = self.list_operations(
                        start=operation, visited=visited, skip_visited=True
                    )
                    for line_operation in line_operations:
                        logging.info('Executing "%s"', line_operation)
                        line = line_operation(line)
                        visited.add(line_operation)
                    yield line

    def list_operations(
        self,
        start: Operation,
        visited: set[Operation],
        skip_visited: bool,
    ):
        """List operations in the ComputationGraph in a BFS fashion.

        Args:
            start: Operation from which to start (not included).
            visited: List of visited nodes.
            skip_visited: Whether to skip visited nodes or not.
        """
        for i, parallel_operations in enumerate(
            nx.bfs_layers(self.operations.graph, start)
        ):
            # Do not include the `start` operation
            if i == 0:
                continue
            for operation in parallel_operations:
                if not skip_visited and operation in visited:
                    continue
                yield operation
