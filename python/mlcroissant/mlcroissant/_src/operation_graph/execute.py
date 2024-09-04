"""Module to execute operations."""

from __future__ import annotations

import collections
from collections.abc import Iterable
import concurrent.futures
import functools
import sys
import typing
from typing import Any, Generator

from absl import logging
import networkx as nx
import pandas as pd

from mlcroissant._src.core.issues import GenerationError
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.operation_graph.base_operation import Operations
from mlcroissant._src.operation_graph.operations import FilterFiles
from mlcroissant._src.operation_graph.operations import ReadFields
from mlcroissant._src.operation_graph.operations.download import Download
from mlcroissant._src.operation_graph.operations.read import Read

if typing.TYPE_CHECKING:
    import apache_beam as beam

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
    group_record_set = next(
        (
            operation
            for operation in operations.nodes
            if isinstance(operation, ReadFields)
            and operation.node.uuid == record_set_id
        )
    )
    ancestors = set(nx.ancestors(operations, group_record_set))
    # Return ReadField and all its ancestors
    return [
        operation
        for operation in nx.topological_sort(operations)
        # If the operation is not a needed operation to compute `record_set`, skip it:
        if operation in ancestors or operation == group_record_set
    ]


def execute_operations_sequentially(record_set: str, operations: Operations):
    """Executes operation and yields results according to the graph of operations."""
    results: dict[Operation, Any] = {}
    for operation in _order_relevant_operations(operations, record_set):
        try:
            previous_results = [
                results[previous_operation]
                for previous_operation in operations.predecessors(operation)
                if previous_operation in results
            ]
            logging.info("Executing %s", operation)
            results[operation] = operation(*previous_results)
            if isinstance(operation, ReadFields):
                if operation.node.uuid != record_set:
                    # The RecordSet will be used later in the graph by another RecordSet
                    # This could be multi-threaded to build the pd.DataFrame faster.
                    results[operation] = pd.DataFrame(list(results[operation]))
                else:
                    # This is the target RecordSet, so we can yield records.
                    yield from results[operation]
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
                yield from operation(result)
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
                            result=operation(file),
                        )

                yield from read_all_files()
                return
            else:
                logging.info("Executing %s", operation)
                if isinstance(operation, ReadFields):
                    continue
                result = operation(result)
        except Exception as e:
            raise GenerationError(
                "An error occured during the streaming generation of the dataset, more"
                f" specifically during the operation {operation}"
            ) from e


def execute_operations_in_beam(
    pipeline: beam.Pipeline, record_set: str, operations: Operations
):
    """See ReadFromCroissant docstring."""
    import apache_beam as beam

    list_of_operations = _order_relevant_operations(operations, record_set)
    queue_of_operations = collections.deque(list_of_operations)
    files = None
    operation = None
    while queue_of_operations:
        operation = queue_of_operations.popleft()
        files = operation(files)
        if isinstance(operation, FilterFiles):
            break
    if not isinstance(files, Iterable):
        raise ValueError("Could not filter files.")
    files = list(files)  # even for large datasets, this can be handled in RAM.

    # We first shard by file and assign a shard_index.
    pipeline = pipeline | "Shard by files with index" >> beam.Create(enumerate(files))
    num_shards = len(files)

    # We don't know in advance the number of records per shards. So we just allocate the
    # maximum number which is `sys.maxsize // num_shards`. For a large evenly
    # distributed dataset, we have:

    # num_shards = number of Parquet files per config on Hugging Face < 10 billion files
    # max_shard_size ~ 1 billion records per Parquet files

    # So it seems we can run with this trick without too many problems. We still trigger
    # a ValueError below if the error arises, and we ask the user to open a bug. A real
    # solution to this problem would be to compute the shard_sizes in parallel of
    # generating the records.
    # TODO(marcenacp): compute shard_sizes explicitly instead of relying on
    # max_shard_size.
    max_shard_size = sys.maxsize // num_shards
    while queue_of_operations:
        operation = queue_of_operations.popleft()
        if isinstance(operation, ReadFields):
            beam_operation = beam.ParDo(
                functools.partial(
                    _add_global_index,
                    operation=operation,
                    max_shard_size=max_shard_size,
                )
            )
        else:
            beam_operation = beam.Map(
                functools.partial(_pass_index, operation=operation)
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
    for index_in_shard, result in enumerate(operation(element)):
        if index_in_shard >= max_shard_size:
            raise ValueError(
                "WARNING: This was very unlikely, but it seems we just hit this limit"
                " in the code. Find another way to optimize execute_operations_in_beam."
                " Please, open a PR on GitHub to make the maintainers aware of this"
                " issue. An actual easy fix is to compute the actual shard_sizes rather"
                " than relying on a heuristic."
            )
        new_index = max_shard_size * shard_index + index_in_shard
        yield (new_index, result)


def _pass_index(
    element_with_index: tuple[int, Any], operation: Operation
) -> ElementWithIndex:
    """Passes the index to the next operation while executing the operation."""
    index, element = element_with_index
    return (index, operation(element))
