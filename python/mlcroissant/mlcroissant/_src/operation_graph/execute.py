"""Module to execute operations."""

import concurrent.futures
from typing import Any

from absl import logging
import networkx as nx
import pandas as pd

from mlcroissant._src.core.issues import GenerationError
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.operation_graph.base_operation import Operations
from mlcroissant._src.operation_graph.operations import ReadFields
from mlcroissant._src.operation_graph.operations.download import Download
from mlcroissant._src.operation_graph.operations.read import Read


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
            previous_results = [
                results[previous_operation]
                for previous_operation in operations.predecessors(operation)
                if previous_operation in results
            ]
            logging.info("Executing %s", operation)
            results[operation] = operation(*previous_results)
            if isinstance(operation, ReadFields):
                if operation.node.name != record_set:
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
                if operation.node.name != record_set:
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
