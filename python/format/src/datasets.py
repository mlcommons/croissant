"""datasets module."""

from collections.abc import Mapping
import dataclasses
import json
from typing import Any, Union

from absl import logging
from etils import epath
from format.src import errors
from format.src import graphs
from format.src.computations import (
    build_structure_graph,
    ComputationGraph,
    GroupRecordSet,
    ReadField,
)
import networkx as nx

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
        """Executes all operations, runs dynamic analysis and yields examples.

        Warning: at the moment, this method yields examples from the first explored
        record_set.
        """
        results: Mapping[str, Any] = {}
        for operation in nx.topological_sort(self.operations.graph):
            logging.info('Executing "%s"', operation)
            kwargs = self.operations.graph.nodes[operation].get("kwargs", {})
            previous_results = [
                results[previous_operation]
                for previous_operation in self.operations.graph.predecessors(operation)
                if previous_operation in results
                # Filter out results that yielded `None`.
                and results[previous_operation] is not None
            ]
            if isinstance(operation, GroupRecordSet):
                yield operation(*previous_results, **kwargs)
            elif isinstance(operation, ReadField):
                assert len(previous_results) == 1, (
                    f'"{operation}" should have one and only one predecessor. Got:'
                    f" {len(previous_results)}."
                )
                previous_result = previous_results[0]
                for _, line in previous_result.iterrows():
                    result = operation(line, **kwargs)
                    yield result
                    results[operation] = result
            else:
                results[operation] = operation(*previous_results, **kwargs)
