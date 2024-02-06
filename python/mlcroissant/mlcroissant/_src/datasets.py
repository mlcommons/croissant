"""datasets module."""

from __future__ import annotations

import dataclasses
from typing import Any, Mapping

from absl import logging
from etils import epath

from mlcroissant._src.core.context import Context
from mlcroissant._src.core.graphs import utils as graphs_utils
from mlcroissant._src.core.issues import ValidationError
from mlcroissant._src.operation_graph import OperationGraph
from mlcroissant._src.operation_graph.execute import execute_downloads
from mlcroissant._src.operation_graph.execute import execute_operations_in_streaming
from mlcroissant._src.operation_graph.execute import execute_operations_sequentially
from mlcroissant._src.structure_graph.nodes.metadata import Metadata


def get_operations(ctx: Context, metadata: Metadata) -> OperationGraph:
    """Returns operations from the metadata."""
    operations = OperationGraph.from_nodes(ctx=ctx, metadata=metadata)
    operations.check_graph()
    if ctx.issues.errors:
        raise ValidationError(ctx.issues.report())
    elif ctx.issues.warnings:
        logging.warning(ctx.issues.report())
    return operations


def _expand_mapping(mapping: Mapping[str, epath.PathLike]) -> Mapping[str, epath.Path]:
    """Expands the file mapping to pathlib-readable paths."""
    return {key: epath.Path(value).expanduser() for key, value in mapping.items()}


@dataclasses.dataclass
class Dataset:
    """Python representation of a Croissant dataset.

    Args:
        jsonld: A JSON object or a path to a Croissant file (URL, str or pathlib.Path).
        debug: Whether to print debug hints. False by default.
        mapping: Mapping filename->filepath as a Python dict[str, str] to handle manual
            downloads. If `document.csv` is the FileObject and you downloaded it to
            `~/Downloads/document.csv`, you can specify `mapping={"document.csv":
            "~/Downloads/document.csv"}`.,
    """

    jsonld: epath.PathLike | str | dict[str, Any] | None
    operations: OperationGraph = dataclasses.field(init=False)
    metadata: Metadata = dataclasses.field(init=False)
    debug: bool = False
    mapping: Mapping[str, epath.PathLike] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        """Runs the static analysis of `file`."""
        ctx = Context()
        ctx.mapping = _expand_mapping(self.mapping)
        if isinstance(self.jsonld, dict):
            self.metadata = Metadata.from_json(ctx=ctx, json_=self.jsonld)
        elif self.jsonld is not None:
            self.metadata = Metadata.from_file(ctx=ctx, file=self.jsonld)
        else:
            return
        # Draw the structure graph for debugging purposes.
        if self.debug:
            graphs_utils.pretty_print_graph(ctx.graph, simplify=True)
        self.operations = get_operations(ctx, self.metadata)
        # Draw the operations graph for debugging purposes.
        if self.debug:
            graphs_utils.pretty_print_graph(self.operations.operations, simplify=False)

    @classmethod
    def from_metadata(cls, metadata: Metadata) -> Dataset:
        """Creates a new `Dataset` from a `Metadata`."""
        dataset = Dataset(jsonld=None)
        dataset.metadata = metadata
        dataset.operations = get_operations(metadata.ctx, metadata)
        return dataset

    def records(self, record_set: str) -> Records:
        """Accesses all records in `record_set` if it exists."""
        if not any(rs for rs in self.metadata.record_sets if rs.name == record_set):
            names = [record_set.name for record_set in self.metadata.record_sets]
            raise ValueError(
                f"did not find any record set with the name {record_set}. Possible"
                f" RecordSets: {names}"
            )
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
