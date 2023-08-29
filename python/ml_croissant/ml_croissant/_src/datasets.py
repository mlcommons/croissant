"""datasets module."""
from __future__ import annotations

import dataclasses

from absl import logging
from etils import epath
import networkx as nx

from ml_croissant._src.core.graphs import utils as graphs_utils
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.core.issues import ValidationError
from ml_croissant._src.core.types import Json
from ml_croissant._src.operation_graph import OperationGraph
from ml_croissant._src.operation_graph.operations import GroupRecordSet
from ml_croissant._src.operation_graph.operations import ReadField
from ml_croissant._src.operation_graph.operations.download import execute_downloads
from ml_croissant._src.structure_graph.nodes.metadata import Metadata


def get_operations(issues: Issues, metadata: Metadata, debug: bool) -> OperationGraph:
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
        self.operations = get_operations(issues, self.metadata, self.debug)
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
        results: Json = {}
        operations = self.dataset.operations.operations
        if self.debug:
            graphs_utils.pretty_print_graph(operations)
        # Downloads can be parallelized, so we execute them in priority.
        execute_downloads(operations)
        for operation in nx.topological_sort(operations):
            if self.debug:
                logging.info('Executing "%s"', operation)
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
                if operation.node.name != self.record_set:
                    continue
                assert len(previous_results) == 1, (
                    f'"{operation}" should have one and only one predecessor. Got:'
                    f" {len(previous_results)}."
                )
                previous_result = previous_results[0]
                for _, line in previous_result.iterrows():
                    read_fields = []
                    for read_field in operations.successors(operation):
                        assert isinstance(read_field, ReadField)
                        if self.debug:
                            logging.info('Executing "%s"', read_field)
                        read_fields.append(read_field(line))
                    if self.debug:
                        logging.info('Executing "%s"', operation)
                    yield operation(*read_fields)
            else:
                if isinstance(operation, ReadField) and not previous_results:
                    continue
                results[operation] = operation(*previous_results)
