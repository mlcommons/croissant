"""Module to execute operations."""

from __future__ import annotations

from collections.abc import Mapping
import concurrent.futures
import functools
import json
import sys
import types
from typing import Any, Generator

from absl import logging
import networkx as nx

from mlcroissant._src.core.issues import GenerationError
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.operation_graph.base_operation import Operations
from mlcroissant._src.operation_graph.operations import FilterFiles
from mlcroissant._src.operation_graph.operations import ReadFields
from mlcroissant._src.operation_graph.operations.download import Download
from mlcroissant._src.operation_graph.operations.read import Read

ElementWithIndex = tuple[int, Any]


def execute_downloads(operations: Operations):
    """Executes all the downloads in the graph of operations."""
    downloads = [
        operation for operation in operations.nodes if isinstance(operation, Download)
    ]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for download in downloads:
            executor.submit(download)


def _order_relevant_operations(
    operations: Operations, record_set_id: str
) -> list[Operation]:
    """Orders all relevant operations for the RecordSet."""
    # ReadFields linked to the `record_set_name`.
    read_fields_operation = next(
        (
            operation
            for operation in operations.nodes
            if isinstance(operation, ReadFields)
            and operation.node.uuid == record_set_id
        )
    )
    ancestors = set(nx.ancestors(operations, read_fields_operation))
    # Return ReadFields and all its ancestors
    return [
        operation
        for operation in nx.topological_sort(operations)
        # If the operation is not a needed operation to compute `record_set`, skip it:
        if operation in ancestors or operation == read_fields_operation
    ]


def execute_operations_sequentially(record_set: str, operations: Operations):
    """Executes operation and yields results according to the graph of operations."""
    for operation in _order_relevant_operations(operations, record_set):
        try:
            logging.info("Executing %s", operation)
            if isinstance(operation, ReadFields) and record_set == operation.node.uuid:
                # This is the target RecordSet, so we can yield records. We don't keep
                # the output in memory, so that we can yield from bigger-than-memory
                # generators.
                yield from operation(set_output_in_memory=False)
            else:
                operation(set_output_in_memory=True)
        except Exception as e:
            raise GenerationError(
                "An error occured during the sequential generation of the dataset, more"
                f" specifically during the operation {operation}"
            ) from e


def execute_operations_in_streaming(
    record_set: str,
    operations: Operations,
    list_of_operations: list[Operation] | None = None,
    result: Any = None,
):
    """Executes operation and streams results when reading files.

    This allows to stream from operations that return a list (e.g., FilterFiles) in
    order not to block on long operations. Instead of downloading the entire dataset,
    we only download the needed files, yield element, then proceed to the next file.
    """
    if list_of_operations is None:
        list_of_operations = _order_relevant_operations(operations, record_set)
    for i, operation in enumerate(list_of_operations):
        try:
            if isinstance(operation, ReadFields):
                if operation.node.uuid != record_set:
                    continue
                yield from operation.call(result)
                return
            elif isinstance(operation, Read):
                # At this stage `result` can be either a Path or a list of Paths.
                if not isinstance(result, list):
                    result = [result]

                def read_all_files():
                    for file in result:
                        # Read files separately and keep executing subsequent operations
                        logging.info("Executing %s", operation)
                        yield from execute_operations_in_streaming(
                            record_set=record_set,
                            operations=operations,
                            list_of_operations=list_of_operations[i + 1 :],
                            result=operation.call(file),
                        )

                yield from read_all_files()
                return
            elif isinstance(result, types.GeneratorType):

                def read_all_items():
                    for item in result:
                        # Read items separately and keep executing subsequent operations
                        logging.info("Executing %s", operation)
                        yield from execute_operations_in_streaming(
                            record_set=record_set,
                            operations=operations,
                            list_of_operations=list_of_operations[i + 1 :],
                            result=operation.call(item),
                        )

                yield from read_all_items()
                return
            else:
                logging.info("Executing %s", operation)
                result = operation.call(result)
        except Exception as e:
            raise GenerationError(
                "An error occured during the streaming generation of the dataset, more"
                f" specifically during the operation {operation}"
            ) from e


def execute_operations_in_beam(
    record_set: str,
    operations: Operations,
    filters: Mapping[str, Any] | None = None,
):
    """See ReadFromCroissant docstring."""
    import apache_beam as beam

    list_of_operations = _order_relevant_operations(operations, record_set)
    target = list_of_operations[-1]
    if not isinstance(target, ReadFields):
        raise ValueError("the target MUST correspond to the RecordSet to generate.")

    # We use the FilterFiles operation to parallelize operations. If there's no
    # FilterFile operation, we set it to `target`.
    filter_files = _find_filter_files(operations, target)
    stage_prefix = f"{record_set} " + json.dumps(filters) if filters else "no filter"

    # In memory = all operations that are not between FilterFiles and the target.
    # In Beam = all operations that are between FilterFiles and the target.
    # Example for a Hugging Face dataset:
    #
    #                         Download(repo)                   Data(splits)
    #                              │                                 │
    #                              ▼                                 │
    #                   FilterFiles(parquet-files)                   │
    #                              │                                 │
    #                              ▼                                 │
    #                 ┌────────────────────────────┐                 ▼
    #                 │      Read(parquet-files)   │         ReadFields(splits)
    #           Those │            │               │                 |
    #      operations │            ▼               │                 |
    #             are │        Join(default)   ◄─────────────────────┘
    #        executed │            │               │
    #     in parallel │            ▼               │
    #         in Beam │    ReadFields(default)     │
    #                 └────────────────────────────┘

    operations_in_memory: list[Operation] = []
    operations_in_beam: list[Operation] = []
    for paths in nx.all_simple_paths(operations, source=filter_files, target=target):
        for operation in paths:
            if operation != filter_files:
                operations_in_beam.append(operation)
    for operation in list_of_operations:
        if operation not in operations_in_beam:
            operations_in_memory.append(operation)

    # Execute all in-memory operations.
    for operation in operations_in_memory:
        # If there is no FilterFiles, we return the PCollection without parallelization.
        if operation == target:
            return beam.Create([(0, *operation.inputs)]) | _beam_operation_with_index(
                operation, sys.maxsize, stage_prefix
            )
        else:
            operation(set_output_in_memory=True)

    files = filter_files.output  # even for large datasets, this can be handled in RAM.
    # We first shard by file and assign a shard_index.
    pipeline = beam.Create(enumerate(files))
    num_shards = len(files)
    if not num_shards:
        raise ValueError(
            f"Empty {record_set=}. No files found for filters={json.dumps(filters)}"
        )

    # We don't know in advance the number of records per shards. So we just allocate the
    # maximum number which is `sys.maxsize // num_shards`. Taking the practical case of
    # large evenly distributed datasets on HuggingFace, we can compute the following:

    # num_shards = number of Parquet files per config on Hugging Face < 10 billion files
    # max_shard_size ~ 1 billion records per Parquet files

    # So it seems we can run with this trick without too many problems. We still trigger
    # a ValueError below if the error arises, and we ask the user to open a bug. A real
    # solution to this problem would be to compute the shard_sizes in parallel of
    # generating the records.
    # TODO(https://github.com/mlcommons/croissant/issues/732): Compute shard_sizes
    # explicitly instead of relying on max_shard_size.
    max_shard_size = sys.maxsize // num_shards
    for operation in operations_in_beam:
        beam_operation = _beam_operation_with_index(
            operation, max_shard_size, stage_prefix
        )
        pipeline |= beam_operation
    return pipeline


def _add_global_index(
    element_with_index: ElementWithIndex,
    operation: Operation,
    max_shard_size: int,
) -> Generator[ElementWithIndex, None, None]:
    """Computes the global index given the shard size."""
    shard_index, element = element_with_index
    for index_in_shard, result in enumerate(operation.call(element)):
        if index_in_shard >= max_shard_size:
            raise ValueError(
                "WARNING: This was very unlikely, but it seems we just hit this limit"
                " in the code. Find another way to optimize execute_operations_in_beam."
                " Please, open a PR on GitHub to make the maintainers aware of this"
                " issue. A fix is to compute the actual shard_sizes rather than relying"
                " on a heuristic (see comments above in code)."
            )
        new_index = max_shard_size * shard_index + index_in_shard
        yield (new_index, result)


def _pass_index(index: int, element: Any, operation: Operation) -> ElementWithIndex:
    """Passes the index to the next operation while executing the operation."""
    return (index, operation.call(element))


def _beam_operation_with_index(
    operation: Operation, max_shard_size: int, stage_prefix: str | None
):
    import apache_beam as beam

    if isinstance(operation, ReadFields):
        return (
            f"{stage_prefix} {operation.node.uuid}: compute the global index."
            >> beam.ParDo(
                functools.partial(
                    _add_global_index,
                    operation=operation,
                    max_shard_size=max_shard_size,
                )
            )
        )
    else:
        return (
            f"{stage_prefix} {operation.node.uuid}: pass the index to the next"
            " operation."
            >> beam.MapTuple(functools.partial(_pass_index, operation=operation))
        )


def _find_filter_files(operations: Operations, target: ReadFields) -> Operation:
    """Finds a FilterFiles operation to parallelize on."""
    filter_files_operations = [
        operation for operation in operations if isinstance(operation, FilterFiles)
    ]
    match len(filter_files_operations):
        case 0:
            return target
        case 1:
            filter_files = filter_files_operations[0]
            if not nx.has_path(operations, source=filter_files, target=target):
                raise NotImplementedError("No path between FilterFiles and the target")
            return filter_files
        case _:
            # If joined branches also have FilterFiles operations, this case is not
            # handled yet. If you have this issue, please open an issue on GitHub.
            raise NotImplementedError("Found several FilterFiles - not handled yet.")
