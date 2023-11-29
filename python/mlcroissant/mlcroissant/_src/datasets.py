"""datasets module."""

from __future__ import annotations

import dataclasses
from typing import Any

from absl import logging
from etils import epath

from mlcroissant._src.core.graphs import utils as graphs_utils
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.core.issues import ValidationError
from mlcroissant._src.operation_graph import OperationGraph
from mlcroissant._src.operation_graph.execute import execute_downloads
from mlcroissant._src.operation_graph.execute import execute_operations_in_streaming
from mlcroissant._src.operation_graph.execute import execute_operations_sequentially
from mlcroissant._src.structure_graph.nodes.metadata import Metadata


def get_operations(issues: Issues, metadata: Metadata) -> OperationGraph:
    """Returns operations from the metadata."""
    graph = metadata.graph
    folder = metadata.folder
    operations = OperationGraph.from_nodes(
        issues=issues,
        metadata=metadata,
        graph=graph,
        folder=folder,
    )
    operations.check_graph()
    if issues.errors:
        raise ValidationError(issues.report())
    elif issues.warnings:
        logging.warning(issues.report())
    return operations


@dataclasses.dataclass
class Dataset:
    """Python representation of a Croissant dataset.

    Args:
        file: A JSON object or a path to a Croissant file (string or pathlib.Path).
        operations: The operation graph class. None by default.
        debug: Whether to print debug hints. False by default.
    """

    file: epath.PathLike | str | dict[str, Any] | None
    operations: OperationGraph = dataclasses.field(init=False)
    metadata: Metadata = dataclasses.field(init=False)
    debug: bool = False

    def __post_init__(self):
        """Runs the static analysis of `file`."""
        issues = Issues()
        if isinstance(self.file, dict):
            self.metadata = Metadata.from_json(
                issues=issues, json_=self.file, folder=None
            )
        elif self.file is not None:
            self.metadata = Metadata.from_file(issues=issues, file=self.file)
        else:
            return
        # Draw the structure graph for debugging purposes.
        if self.debug:
            graphs_utils.pretty_print_graph(self.metadata.graph, simplify=True)
        self.operations = get_operations(issues, self.metadata)
        # Draw the operations graph for debugging purposes.
        if self.debug:
            graphs_utils.pretty_print_graph(self.operations.operations, simplify=False)

    @classmethod
    def from_metadata(cls, metadata: Metadata) -> Dataset:
        """Creates a new `Dataset` from a `Metadata`."""
        dataset = Dataset(file=None)
        dataset.metadata = metadata
        dataset.operations = get_operations(metadata.issues, metadata)
        return dataset

    def records(self, record_set: str) -> Records:
        """Accesses all records in `record_set` if it exists."""
        if not any(rs for rs in self.metadata.record_sets if rs.name == record_set):
            raise ValueError(f"did not find any record set with the name {record_set}.")
        return Records(self, record_set, debug=self.debug)


@dataclasses.dataclass
class Records:
    """Iterable set of records.

    Args:
        dataset: The parent dataset.
        record_set: The name of the record set.
        debug: Whether to print debug hints.
    """

    dataset: Dataset
    record_set: str
    debug: bool

    def __iter__(self):
        """Executes all operations, runs dynamic analysis and yields examples.

        Warning: at the moment, this method yields examples from the first explored
        record_set.
        """
        operations = self.dataset.operations.operations
        if self.debug:
            graphs_utils.pretty_print_graph(operations)
        # Downloads can be parallelized, so we execute them in priority.
        execute_downloads(operations)
        # We can stream the dataset iff the operation graph is a path graph (meaning
        # that all operations lie on a single straight line, i.e. have an
        # in-degree of 0 or 1. That means that the operation graph is a single line
        # (without external joins for example).
        can_stream_dataset = all(d == 1 or d == 2 for _, d in operations.degree())
        if can_stream_dataset:
            yield from execute_operations_in_streaming(
                record_set=self.record_set,
                operations=operations,
            )
        else:
            yield from execute_operations_sequentially(
                record_set=self.record_set, operations=operations
            )
