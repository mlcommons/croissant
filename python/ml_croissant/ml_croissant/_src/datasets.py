"""datasets module."""
from __future__ import annotations

import dataclasses

from absl import logging
from etils import epath
import networkx as nx

from ml_croissant._src.core.graphs import utils as graphs_utils
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.core.issues import ValidationError
from ml_croissant._src.operation_graph import OperationGraph
from ml_croissant._src.operation_graph.execute import execute_downloads
from ml_croissant._src.operation_graph.execute import execute_operations_in_streaming
from ml_croissant._src.operation_graph.execute import execute_operations_sequentially
from ml_croissant._src.operation_graph.operations import GroupRecordSet
from ml_croissant._src.structure_graph.nodes.metadata import Metadata


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

    file: epath.PathLike
    operations: OperationGraph = dataclasses.field(init=False)
    metadata: Metadata = dataclasses.field(init=False)
    debug: bool = False

    def __post_init__(self):
        """Runs the static analysis of `file`."""
        issues = Issues()
        self.metadata = Metadata.from_file(issues=issues, file=self.file)
        # Draw the structure graph for debugging purposes.
        if self.debug:
            graphs_utils.pretty_print_graph(self.metadata.graph, simplify=True)
        self.operations = get_operations(issues, self.metadata)
        # Draw the operations graph for debugging purposes.
        if self.debug:
            graphs_utils.pretty_print_graph(self.operations.operations, simplify=False)

    def records(self, record_set: str) -> Records:
        """Accesses all records belonging to the RecordSet named `record_set`."""
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
        can_stream_dataset = all(
            d == 1 or d == 2
            for operation, d in operations.degree()
            if not isinstance(operation, GroupRecordSet)
        )
        if can_stream_dataset:
            yield from execute_operations_in_streaming(
                record_set=self.record_set,
                operations=operations,
                list_of_operations=list(nx.topological_sort(operations)),
            )
        else:
            yield from execute_operations_sequentially(
                record_set=self.record_set, operations=operations
            )
