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
from ml_croissant._src.structure_graph.graph import Structure
from ml_croissant._src.structure_graph.nodes.metadata import Metadata


@dataclasses.dataclass
class Dataset:
    """Python representation of a Croissant dataset.

    Args:
        file: A JSON object or a path to a Croissant file (string or pathlib.Path).
        metadata: The metadata of the dataset.
        debug: Whether to print debug hints. False by default.

    Usage:

    - To build a `Dataset` from a file:

    ```python
    dataset = mlc.Dataset(file="/path/to/croissant.json")
    ```

    - To build a `Dataset` from programmatic metadata:

    ```python
    dataset = mlc.Dataset(
        metadata=mlc.nodes.Metadata(...),
    )
    ```
    """

    file: epath.PathLike | None = None
    metadata: Metadata | None = None
    debug: bool = False
    operations: OperationGraph = dataclasses.field(init=False)

    def __post_init__(self):
        """Runs the static analysis of `file`."""
        issues = Issues()
        if self.file is not None and self.metadata is None:
            structure = Structure.from_file(issues=issues, file=self.file)
            self.metadata = structure.metadata
        elif self.file is None and self.metadata is not None:
            structure = Structure(issues=issues, metadata=self.metadata)
        else:
            raise ValueError(
                "New `Dataset` instance needs either `file` or `metadata`. See the"
                " docstring for more information."
            )
        try:
            filepath, graph, metadata = (
                structure.filepath,
                structure.graph,
                structure.metadata,
            )
            folder = filepath.parent
            structure.check_graph()
            # Draw the structure graph for debugging purposes.
            if self.debug:
                graphs_utils.pretty_print_graph(graph, simplify=True)
            self.operations = OperationGraph.from_nodes(
                issues=issues,
                metadata=metadata,
                graph=graph,
                folder=folder,
            )
            self.operations.check_graph()
        except Exception as exception:
            if issues.errors:
                raise ValidationError(issues.report()) from exception
            raise exception
        if issues.errors:
            raise ValidationError(issues.report())
        elif issues.warnings:
            logging.warning(issues.report())

    def to_json(self) -> Json:
        """Converts the `Dataset` to JSON."""
        return self.metadata.to_json()

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
