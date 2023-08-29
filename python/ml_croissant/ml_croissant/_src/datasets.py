"""datasets module."""
from __future__ import annotations

import dataclasses
from typing import Any

from absl import logging
from etils import epath
import networkx as nx

from ml_croissant._src.core.graphs import utils as graphs_utils
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.core.issues import ValidationError
from ml_croissant._src.core.types import Json
from ml_croissant._src.operation_graph import OperationGraph
from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.operation_graph.operations import GroupRecordSet
from ml_croissant._src.operation_graph.operations import ReadField
from ml_croissant._src.operation_graph.operations.download import execute_downloads
from ml_croissant._src.operation_graph.operations.read import Read
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


def execute_operations_sequentially(record_set: str, operations: nx.MultiDiGraph):
    """Executes operation and yields results according to the graph of operations."""
    results: Json = {}
    for operation in nx.topological_sort(operations):
        logging.debug('Executing "%s"', operation)
        previous_results = [
            results[previous_operation]
            for previous_operation in operations.predecessors(operation)
            if previous_operation in results
            # Filter out results that yielded `None`.
            and results[previous_operation] is not None
        ]
        if isinstance(operation, GroupRecordSet):
            # Only keep the record set whose name is `self.record_set`.
            # Note: this is a short-term solution. The long-term solution is to
            # re-compute the sub-graph of operations that is sufficient to compute
            # `self.record_set`.
            if operation.node.name != record_set:
                continue
            yield from build_record_set(operations, operation, previous_results)
        else:
            if isinstance(operation, ReadField) and not previous_results:
                continue
            results[operation] = operation(*previous_results)


def execute_operations_in_streaming(
    record_set: str,
    operations: nx.DiGraph,
    list_of_operations: list[Operation],
    result: Any = None,
):
    """Executes operation and streams results when reading files.

    This allows to stream from operations that return a list (e.g., FilterFiles) in
    order not to block on long operations. Instead of downloading the entire dataset,
    we only download the needed files, yield element, then proceed to the next file.
    """
    for i, operation in enumerate(list_of_operations):
        if isinstance(operation, GroupRecordSet):
            if operation.node.name != record_set:
                continue
            yield from build_record_set(operations, operation, result)
            return
        elif isinstance(operation, Read):
            # At this stage `result` can be either a Path or a list of Paths.
            if not isinstance(result, list):
                result = [result]
            for file in result:
                # Read files separately and keep executing all subsequent operations.
                logging.info("Executing %s", operation)
                read_file = operation(file)
                yield from execute_operations_in_streaming(
                    record_set=record_set,
                    operations=operations,
                    list_of_operations=list_of_operations[i + 1 :],
                    result=[read_file],
                )
                return
        else:
            logging.info("Executing %s", operation)
            if isinstance(operation, ReadField):
                continue
            result = operation(result)


def build_record_set(
    operations: nx.MultiDiGraph, operation: GroupRecordSet, result: Any
):
    """Builds a RecordSet from all ReadField children in the operation graph."""
    assert (
        len(result) == 1
    ), f'"{operation}" should have one and only one predecessor. Got: {len(result)}.'
    result = result[0]
    for _, line in result.iterrows():
        read_fields = []
        for read_field in operations.successors(operation):
            assert isinstance(read_field, ReadField)
            read_fields.append(read_field(line))
        logging.info("Executing %s", operation)
        yield operation(*read_fields)
