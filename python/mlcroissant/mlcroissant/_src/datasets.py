"""datasets module."""

from __future__ import annotations

from collections.abc import Mapping
import dataclasses
import re
import typing
from typing import Any

from absl import logging
from etils import epath
import networkx as nx

from mlcroissant._src.core.context import Context
from mlcroissant._src.core.graphs import utils as graphs_utils
from mlcroissant._src.core.issues import ValidationError
from mlcroissant._src.operation_graph import OperationGraph
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.operation_graph.base_operation import Operations
from mlcroissant._src.operation_graph.execute import execute_downloads
from mlcroissant._src.operation_graph.execute import execute_operations_in_beam
from mlcroissant._src.operation_graph.execute import execute_operations_in_streaming
from mlcroissant._src.operation_graph.execute import execute_operations_sequentially
from mlcroissant._src.operation_graph.operations import FilterFiles
from mlcroissant._src.operation_graph.operations import InitOperation
from mlcroissant._src.operation_graph.operations import ReadFields
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.metadata import Metadata
from mlcroissant._src.structure_graph.nodes.source import FileProperty

if typing.TYPE_CHECKING:
    import apache_beam as beam

Filters = Mapping[str, Any]


def get_operations(ctx: Context, metadata: Metadata) -> OperationGraph:
    """Returns operations from the metadata."""
    operations = OperationGraph.from_nodes(ctx=ctx, metadata=metadata)
    operations.check_graph(ctx=ctx)
    if ctx.issues.errors:
        raise ValidationError(ctx.issues.report())
    elif ctx.issues.warnings:
        logging.warning(ctx.issues.report())
    return operations


def _check_mapping(metadata: Metadata, mapping: Mapping[str, epath.Path]):
    """Checks that the mapping is valid, i.e. keys are actual UUIDs and paths exist."""
    uuids = set([node.uuid for node in metadata.nodes()])
    for uuid, path in mapping.items():
        if uuid not in uuids:
            raise ValueError(f"{uuid=} in the mapping doesn't exist in the JSON-LD")
        if not path.exists():
            raise ValueError(f"{path=} doesn't exist on disk")


def _expand_mapping(
    mapping: Mapping[str, epath.PathLike] | None,
) -> Mapping[str, epath.Path]:
    """Expands the file mapping to pathlib-readable paths."""
    if isinstance(mapping, Mapping):
        return {key: epath.Path(value).expanduser() for key, value in mapping.items()}
    return {}


@dataclasses.dataclass
class Dataset:
    """Python representation of a Croissant dataset.

    Args:
        jsonld: A JSON object or a path to a Croissant file (URL, str or pathlib.Path).
        debug: Whether to print debug hints. False by default.
        mapping: Mapping filename->filepath as a Python dict[str, str] to handle manual
            downloads. If `document.csv` is the FileObject and you downloaded it to
            `~/Downloads/document.csv`, you can specify `mapping={"document.csv":
            "~/Downloads/document.csv"}`.
    """

    jsonld: epath.PathLike | str | dict[str, Any] | None
    operations: OperationGraph = dataclasses.field(init=False)
    metadata: Metadata = dataclasses.field(init=False)
    debug: bool = False
    mapping: Mapping[str, epath.PathLike] | None = None

    def __post_init__(self):
        """Runs the static analysis of `file`."""
        ctx = Context(mapping=_expand_mapping(self.mapping))
        if isinstance(self.jsonld, dict):
            self.metadata = Metadata.from_json(ctx=ctx, json_=self.jsonld)
        elif self.jsonld is not None:
            self.metadata = Metadata.from_file(ctx=ctx, file=self.jsonld)
        else:
            return
        _check_mapping(self.metadata, ctx.mapping)
        # Draw the structure graph for debugging purposes.
        if self.debug:
            graphs_utils.pretty_print_graph(ctx.graph)
        self.operations = get_operations(ctx, self.metadata)
        # Draw the operations graph for debugging purposes.
        if self.debug:
            graphs_utils.pretty_print_graph(self.operations.operations)

    @classmethod
    def from_metadata(cls, metadata: Metadata) -> Dataset:
        """Creates a new `Dataset` from a `Metadata`."""
        dataset = Dataset(jsonld=None)
        dataset.metadata = metadata
        dataset.operations = get_operations(metadata.ctx, metadata)
        return dataset

    def records(self, record_set: str, filters: Filters | None = None) -> Records:
        """Accesses all records with @id==record_set if it exists.

        record_set: The name of the record set to access.
        filters: A dictionary mapping a field ID to the value we want to filter in. For
            example, when writing {'data/split': 'train'}, we want to keep all records
            whose field `data/split` takes the value `train`.
        """
        if filters:
            _validate_filters(filters)

        if not any(rs for rs in self.metadata.record_sets if rs.uuid == record_set):
            ids = [record_set.uuid for record_set in self.metadata.record_sets]
            error_msg = f"did not find any record set with the name `{record_set}`. "
            if not ids:
                error_msg += "This dataset declares no record sets."
            else:
                error_msg += f"Possible RecordSets: {ids}"
            raise ValueError(error_msg)
        return Records(
            dataset=self,
            record_set=record_set,
            filters=filters,
            debug=self.debug,
        )


@dataclasses.dataclass(kw_only=True)
class Records:
    """Iterable set of records.

    Args:
        dataset: The parent dataset.
        record_set: The name of the record set.
        debug: Whether to print debug hints.
    """

    dataset: Dataset
    record_set: str
    filters: Filters | None
    debug: bool

    def __iter__(self):
        """Executes all operations, runs dynamic analysis and yields examples.

        Warning: at the moment, this method yields examples from the first explored
        record_set.
        """
        # We only consider the operations that are useful to produce the `ReadFields`.
        operations = self._filter_interesting_operations(self.filters)
        # Downloads can be parallelized, so we execute them in priority.
        execute_downloads(operations)
        # We can stream the dataset iff the operation graph is a path graph (meaning
        # that all operations lie on a single straight line, i.e. have an
        # in-degree of 0 or 1. That means that the operation graph is a single line
        # (without external joins for example).
        if _is_streamable_dataset(operations):
            yield from execute_operations_in_streaming(
                record_set=self.record_set,
                operations=operations,
            )
        else:
            yield from execute_operations_sequentially(
                record_set=self.record_set, operations=operations
            )

    def beam_reader(
        self, pipeline: beam.Pipeline, filters: Mapping[str, Any] | None = None
    ):
        """See ReadFromCroissant docstring."""
        operations = self._filter_interesting_operations(self.filters)
        execute_downloads(operations)
        return execute_operations_in_beam(
            pipeline=pipeline,
            record_set=self.record_set,
            operations=operations,
            filters=filters or self.filters,
        )

    def _filter_interesting_operations(self, filters: Filters | None) -> Operations:
        """Filters connected operations to `ReadFields(self.record_set)`.

        This function does 2 things:

        - It keeps only the operations that are necessary to produce the record set.
        - It applies the filters to all operations. Example: if we request the training
          set, it will only download the data relative to the training set.
        """
        operations = self.dataset.operations.operations
        source = next(
            operation
            for operation in operations.nodes
            if isinstance(operation, InitOperation)
        )
        target = next(
            operation
            for operation in operations.nodes
            if isinstance(operation, ReadFields)
            and operation.node.uuid == self.record_set
        )
        paths = nx.all_simple_paths(operations, source=source, target=target)
        interesting_nodes = {node for path in paths for node in path}
        interesting_operations = operations.subgraph(interesting_nodes)
        if not filters:
            return interesting_operations  # pytype: disable=bad-return-type
        field, value = _find_data_field_to_filter(filters, interesting_operations)
        new_regex = _regex_from_value(field, value)
        _propagate_includes(field, interesting_operations, new_regex)
        return interesting_operations  # pytype: disable=bad-return-type


def _find_data_field_to_filter(
    filters: Filters, operations: nx.Graph[Operation]
) -> tuple[Field, Any]:
    for operation in operations:
        if isinstance(operation, ReadFields):
            for field in operation.node.fields:
                if field.uuid in filters:
                    return field, filters[field.id]
    raise ValueError(
        f"Filters ({filters}) do not apply to the fields. `filters` must be a"
        " mapping from the field ID to the value to filter in, e.g. `{'split':"
        " 'train'}` to filter the train split."
    )


def _regex_to_glob(regex: str) -> str:
    """Converts a regular expression to a blob pattern by unescaping regex syntax.

    Warning: this is based on manual heuristics to convert a regular expression to a
    glob expression.
    """
    # Remove starting ^
    regex = re.sub(r"^\^", "", regex)
    # Remove trailing $
    regex = re.sub(r"\$$", "", regex)
    # Interpret \. as .
    regex = re.sub(r"\\\.", ".", regex)
    # Interpret .* as *
    regex = re.sub(r"\.\*", "*", regex)
    # Interpret .+ as *
    regex = re.sub(r"\.\+", "*", regex)
    return regex


def _regex_from_value(field: Field, value: Any):
    """Creates a regular expression by injecting the value in the transformation."""
    transforms = field.source.transforms
    error = (
        "Filtering is currently only implemented on fields with one transformation from"
        " a regex."
    )
    if len(transforms) != 1:
        raise NotImplementedError(error)
    transform = transforms[0]
    if str_regex := transform.regex:
        capturing_groups = re.compile(r"\(.*\)")
        groups = capturing_groups.findall(str_regex)
        if len(groups) == 1:
            # Check that the value respects the expected capturing group:
            re.match(groups[0], value)
        else:
            raise ValueError(
                "A transform regex should have exactly 1 capturing group in"
                f" the transform regex. Got: '{str_regex}'"
            )
        return capturing_groups.sub(re.escape(value), str_regex)
    raise NotImplementedError(error)


def _propagate_includes(field: Field, operations: nx.Graph[Operation], new_regex: str):
    """Propagates the new_regex back to the source includes.

    Warning: the following lines are a heuristic to inject the regex in the glob
    pattern. First we split the glob pattern by `/` hoping that the filename glob
    pattern comes after this `/`. Here is an example, with the name of the variables and
    a possible example:

    pattern   ->  filename_pattern  ->  filename   ->  new_pattern
    **/*.jpg  ->  *.jpg             ->  train.jpg  ->  **/train.jpg

    Then, we update in place the nodes with the new pattern.
    """
    source_uuid = field.source.uuid
    error = (
        "Currently, filtering is only implemented when extracting a"
        " field from its filename or fullpath. Please, open a GitHub"
        " issue if you want support for other extract."
    )
    source_type = field.source.extract.file_property
    if not field.source.extract.file_property:
        raise NotImplementedError(error)
    for operation in operations:
        if isinstance(operation, FilterFiles):
            node = operation.node
            if node.uuid == source_uuid and new_regex:
                includes = node.includes or []
                if source_type == FileProperty.filename:
                    new_includes = []
                    for pattern in includes:
                        filename_pattern = pattern.split("/")
                        if len(filename_pattern) <= 1:
                            raise NotImplementedError()
                        filename = _regex_to_glob(new_regex)
                        new_pattern = filename_pattern[:-1] + [filename]
                        new_includes.append("/".join(new_pattern))
                    node.includes = new_includes
                elif source_type == FileProperty.fullpath:
                    node.includes = [_regex_to_glob(new_regex) for _ in includes]
                else:
                    raise NotImplementedError(error)


def _validate_filters(filters: Filters):
    if isinstance(filters, Mapping) and len(filters) <= 1:
        if all(isinstance(value, str) for value in filters.values()):
            return
    raise ValueError(
        "Filters should be a mapping from a field's ID to the value we want to"
        " filter in. For example, when writing {'data/split': 'train'}, we want"
        " to keep all records whose field `data/split` takes the value `train`."
        f" Instead, we got: {filters=}"
    )


def _is_streamable_dataset(operations: Operations):
    """Whether the operations define a streamable datasets.

    A streamable dataset is a dataset that results from executing a linear sequence of
    operations without branching (for example, no join).
    """
    return all(d == 1 or d == 2 for _, d in operations.degree())
