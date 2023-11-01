"""Module to execute operations."""

import concurrent.futures
from typing import Any

from absl import logging
import networkx as nx
import pandas as pd

from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.operation_graph.base_operation import Operations
from mlcroissant._src.operation_graph.operations import GroupRecordSetEnd
from mlcroissant._src.operation_graph.operations import GroupRecordSetStart
from mlcroissant._src.operation_graph.operations import ReadField
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
    # GroupRecordSetEnd linked to the `record_set_name`.
    group_record_set = next(
        (
            operation
            for operation in operations.nodes
            if isinstance(operation, GroupRecordSetEnd)
            and operation.node.name == record_set_name
        )
    )
    ancestors = set(nx.ancestors(operations, group_record_set))
    return [
        operation
        for operation in nx.topological_sort(operations)
        # If the operation is not a needed operation to compute `record_set`, skip it:
        if operation in ancestors
    ]


def execute_operations_sequentially(record_set: str, operations: Operations):
    """Executes operation and yields results according to the graph of operations."""
    results: dict[Operation, Any] = {}
    for operation in _order_relevant_operations(operations, record_set):
        previous_results = [
            results[previous_operation]
            for previous_operation in operations.predecessors(operation)
            if previous_operation in results
            # Filter out results that yielded `None`.
            and results[previous_operation] is not None
        ]
        if isinstance(operation, GroupRecordSetStart):
            assert len(previous_results) == 1, (
                f'"{operation}" should have one and only one predecessor. Got:'
                f" {len(previous_results)}."
            )
            result = previous_results[0]
            built_record_set = build_record_set(operations, operation, result)
            if operation.node.name != record_set:
                # The RecordSet will be used later in the graph by another RecordSet.
                # This could be multi-threaded to build the pd.DataFrame faster.
                built_record_set = pd.DataFrame(list(built_record_set))
                if not built_record_set.empty:
                    results[operation] = built_record_set
                    # Propagate the result to all `ReadField` children.
                    for successor in operations.successors(operation):
                        results[successor] = built_record_set
            else:
                # This is the target RecordSet, so we can yield records.
                yield from built_record_set
        elif isinstance(operation, GroupRecordSetEnd):
            if operation.node.name != record_set:
                logging.info("Executing %s", operation)
                results[operation] = operation(*previous_results)
        elif not isinstance(operation, ReadField):
            logging.info("Executing %s", operation)
            results[operation] = operation(*previous_results)


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
        if isinstance(operation, GroupRecordSetStart):
            if operation.node.name != record_set:
                continue
            yield from build_record_set(operations, operation, result)
            return
        elif isinstance(operation, Read):
            # At this stage `result` can be either a Path or a list of Paths.
            if not isinstance(result, list):
                result = [result]

            def read_all_files():
                for file in result:
                    # Read files separately and keep executing subsequent operations.
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
            if isinstance(operation, ReadField):
                continue
            result = operation(result)


def build_record_set(
    operations: Operations, operation: GroupRecordSetStart, result: pd.DataFrame
):
    """Builds a RecordSet from all ReadField children in the operation graph."""
    for _, line in result.iterrows():
        read_fields = []
        for read_field in operations.successors(operation):
            assert isinstance(read_field, ReadField)
            read_fields.append(read_field(line))
        logging.info("Executing %s", operation)
        yield from operation(*read_fields)
