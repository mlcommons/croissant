"""Module to execute operations."""

import concurrent.futures
import dataclasses
from typing import Any

from absl import logging
import networkx as nx
import pandas as pd

from mlcroissant._src.core.issues import GenerationError
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.operation_graph.base_operation import Operations
from mlcroissant._src.operation_graph.operations import FilterFiles
from mlcroissant._src.operation_graph.operations import Read
from mlcroissant._src.operation_graph.operations import ReadFields
from mlcroissant._src.operation_graph.operations.download import Download


def execute_downloads(operations: Operations):
    """Executes all the downloads in the graph of operations."""
    downloads = [
        operation for operation in operations.nodes if isinstance(operation, Download)
    ]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for download in downloads:
            executor.submit(download)


def _order_relevant_operations(
    operations: Operations, record_set_name: str
) -> list[Operation]:
    """Orders all relevant operations for the RecordSet."""
    # ReadFields linked to the `record_set_name`.
    group_record_set = next(
        (
            operation
            for operation in operations.nodes
            if isinstance(operation, ReadFields)
            and operation.node.name == record_set_name
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
            previous_results = operation.previous_results(results)
            logging.info("Executing %s", operation)
            results[operation] = operation(*previous_results)
            if isinstance(operation, ReadFields):
                if operation.node.name != record_set:
                    # The RecordSet will be used later in the graph by another RecordSet.
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


@dataclasses.dataclass
class _GeneratorManager:
    """Implements a state manager to propagate that the iteration must stop."""

    should_continue: bool = True


def execute_operations_in_streaming(
    record_set: str,
    operations: Operations,
    list_of_operations: list[Operation] | None = None,
    results: dict[Operation, Any] = dict(),
):
    """Executes operation and streams results when reading files.

    This allows to stream from operations that return a list (e.g., FilterFiles) in
    order not to block on long operations. Instead of downloading the entire dataset,
    we only download the needed files, yield element, then proceed to the next file.
    """
    manager = _GeneratorManager()
    if list_of_operations is None:
        list_of_operations = _order_relevant_operations(operations, record_set)
    for i, operation in enumerate(list_of_operations):
        try:
            previous_results = operation.previous_results(results)

            if isinstance(operation, ReadFields):
                yield from operation(*previous_results)
                return

            def execute_operation_on_rows():
                is_file_operation = isinstance(operation, (FilterFiles, Read))
                if is_file_operation:
                    for row in previous_results:
                        logging.info("Executing %s", operation)
                        result = operation(row)
                        results[operation] = result
                        yield from execute_operations_in_streaming(
                            record_set=record_set,
                            operations=operations,
                            list_of_operations=list_of_operations[i + 1 :],
                            results=results,
                        )
                        manager.should_continue = False
                else:
                    logging.info("Executing %s", operation)
                    result = operation(*previous_results)
                    results[operation] = result

            yield from execute_operation_on_rows()
            if not manager.should_continue:
                return
        except Exception as e:
            raise GenerationError(
                "An error occured during the streaming generation of the dataset, more"
                f" specifically during the operation {operation}"
            ) from e
