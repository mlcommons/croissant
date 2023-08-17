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
from ml_croissant._src.operation_graph import OperationGraph
from ml_croissant._src.operation_graph.operations import GroupRecordSet
from ml_croissant._src.operation_graph.operations import ReadField
from ml_croissant._src.operation_graph.operations.download import execute_downloads
from ml_croissant._src.structure_graph.graph import check_structure_graph
from ml_croissant._src.structure_graph.graph import from_file_to_json
from ml_croissant._src.structure_graph.graph import from_json_to_rdf
from ml_croissant._src.structure_graph.graph import from_nodes_to_structure_graph
from ml_croissant._src.structure_graph.graph import from_rdf_to_nodes


@dataclasses.dataclass
class Validator:
    """Static analysis of the issues in the Croissant file."""

    file_or_file_path: epath.PathLike
    issues: Issues = dataclasses.field(default_factory=Issues)
    file: dict = dataclasses.field(init=False)
    operations: OperationGraph | None = None

    def run_static_analysis(self, debug: bool = False):
        """Runs the static analysis on the file."""
        try:
            file_path, self.file = from_file_to_json(self.file_or_file_path)
            folder = file_path.parent
            json_ld = from_json_to_rdf(self.file)
            graph = from_rdf_to_nodes(self.issues, json_ld, folder)
            # Print all nodes for debugging purposes.
            if debug:
                logging.info("Found the following nodes during static analysis.")
                for node in graph.nodes:
                    logging.info(node)
            metadata, graph = from_nodes_to_structure_graph(self.issues, graph)
            check_structure_graph(self.issues, graph)
            # Draw the structure graph for debugging purposes.
            if debug:
                graphs_utils.pretty_print_graph(graph, simplify=True)
            self.operations = OperationGraph.from_nodes(
                issues=self.issues,
                metadata=metadata,
                graph=graph,
                folder=file_path.parent,
            )
            self.operations.check_graph()
        except Exception as exception:
            if self.issues.errors:
                raise ValidationError(self.issues.report()) from exception
            raise exception
        if self.issues.errors:
            raise ValidationError(self.issues.report())
        elif self.issues.warnings:
            logging.warning(self.issues.report())


@dataclasses.dataclass
class Dataset:
    """Python representation of a Croissant dataset.

    Args:
        file: A JSON object or a path to a Croissant file (string or pathlib.Path).
        operations: The operation graph class. None by default.
        debug: Whether to print debug hints. False by default.
    """

    file: epath.PathLike
    operations: OperationGraph | None = None
    debug: bool = False

    def __post_init__(self):
        """Runs the static analysis of `file`."""
        self.validator = Validator(self.file)
        self.validator.run_static_analysis(debug=self.debug)
        self.file = self.validator.file
        self.operations = self.validator.operations

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
        results: dict[str, Any] = {}
        operations = self.dataset.operations.operations
        if self.debug:
            graphs_utils.pretty_print_graph(operations)
        # Downloads can be parallelized, so we execute them in priority.
        execute_downloads(operations)
        for operation in nx.topological_sort(operations):
            if self.debug:
                logging.info('Executing "%s"', operation)
            kwargs = operations.nodes[operation].get("kwargs", {})
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
                        read_fields.append(read_field(line, **kwargs))
                    if self.debug:
                        logging.info('Executing "%s"', operation)
                    yield operation(*read_fields, **kwargs)
            else:
                if isinstance(operation, ReadField) and not previous_results:
                    continue
                results[operation] = operation(*previous_results, **kwargs)
