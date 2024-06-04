"""graph module."""

import dataclasses

from etils import epath
import networkx as nx

from mlcroissant._src.core.constants import EncodingFormat
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.operation_graph.base_operation import Operations
from mlcroissant._src.operation_graph.operations import Concatenate
from mlcroissant._src.operation_graph.operations import Data
from mlcroissant._src.operation_graph.operations import Download
from mlcroissant._src.operation_graph.operations import Extract
from mlcroissant._src.operation_graph.operations import FilterFiles
from mlcroissant._src.operation_graph.operations import InitOperation
from mlcroissant._src.operation_graph.operations import Join
from mlcroissant._src.operation_graph.operations import LocalDirectory
from mlcroissant._src.operation_graph.operations import Read
from mlcroissant._src.operation_graph.operations import ReadFields
from mlcroissant._src.operation_graph.operations.extract import should_extract
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.base_node import node_by_uuid
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.file_object import FileObject
from mlcroissant._src.structure_graph.nodes.file_set import FileSet
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet


def _find_record_set(node: Node) -> RecordSet:
    """Finds the record set to which a field is attached.

    The record set will be typically either the parent or the parent's parent.
    """
    for parent in reversed(node.parents):
        if isinstance(parent, RecordSet):
            return parent
    raise ValueError(f"Node {node} has no RecordSet parent.")


def _add_operations_for_record_set(
    operations: Operations,
    record_set: RecordSet,
):
    """Adds all operations for a node of type `RecordSet`."""
    if record_set.data:
        Data(operations=operations, node=record_set) >> ReadFields(
            operations=operations, node=record_set
        )
    has_join = any(field for field in record_set.fields if field.references.uuid)
    if has_join:
        Join(operations=operations, node=record_set) >> ReadFields(
            operations=operations, node=record_set
        )
    else:
        ReadFields(operations=operations, node=record_set)


def _add_operations_for_file_object(
    operations: Operations,
    node: FileObject,
    folder: epath.Path,
):
    """Adds all operations for a node of type `FileObject`.

    Operations are:

    - `Download`.
    - `Extract` if the file needs to be extracted.
    - `Concatenate` to merge several dataframes into one.
    - `Read` to read the file if it's a CSV.
    """
    operation: Operation | None = None
    if not node.contained_in:
        # Download the file
        operation = Download(operations=operations, node=node)
    first_operation = operation
    for successor in node.successors:
        # Reset `operation` to be the very first operation at each loop.
        operation = first_operation
        # Extract the file if needed
        if (
            should_extract(node.encoding_format)
            and isinstance(successor, (FileObject, FileSet))
            and not should_extract(successor.encoding_format)
        ):
            operation = operation >> Extract(operations=operations, node=node)
        if isinstance(successor, FileSet):
            operation = (
                operation
                >> FilterFiles(operations=operations, node=successor)
                >> Concatenate(operations=operations, node=successor)
            )
        if node.encoding_format and not should_extract(node.encoding_format):
            fields = tuple([
                field for field in node.recursive_successors if isinstance(field, Field)
            ])
            operation >> Read(
                operations=operations,
                node=node,
                folder=folder,
                fields=fields,
            )


def _add_operations_for_git(
    operations: Operations,
    node: FileObject,
    folder: epath.Path,
):
    """Adds all operations for a FileObject reading from a Git repository."""
    operation = Download(operations=operations, node=node)
    for successor in node.successors:
        if isinstance(successor, FileSet):
            fields = tuple(
                field
                for field in successor.recursive_successors
                if isinstance(field, Field)
            )
            (
                operation
                >> FilterFiles(operations=operations, node=successor)
                >> Read(
                    operations=operations,
                    node=successor,
                    folder=folder,
                    fields=fields,
                )
            )


def _add_operations_for_local_file_sets(
    operations: Operations,
    node: FileSet,
    folder: epath.Path,
):
    """Adds all operations for a FileSet reading from local files."""
    fields = tuple([
        field for field in node.recursive_successors if isinstance(field, Field)
    ])
    (
        LocalDirectory(
            operations=operations,
            node=node,
            folder=folder,
        )
        >> FilterFiles(operations=operations, node=node)
        >> Read(
            operations=operations,
            node=node,
            folder=folder,
            fields=fields,
        )
    )


def _add_operations_for_field(operations: Operations, node: Field):
    """Adds all joins for a Field."""
    record_set = _find_record_set(node)
    joins = [
        operation
        for operation in operations.nodes
        if isinstance(operation, Join) and operation.node == record_set
    ]
    for join in joins:
        left_node = node_by_uuid(node.ctx, node.source.uuid)
        right_node = node_by_uuid(node.ctx, node.references.uuid)
        if left_node and right_node:
            join.connect_to_last_operation(left_node)
            join.connect_to_last_operation(right_node)


@dataclasses.dataclass(frozen=True)
class OperationGraph:
    """Graph of dependent operations to execute to generate the dataset."""

    issues: Issues
    operations: Operations

    @classmethod
    def from_nodes(cls, ctx: Context, metadata: Node) -> "OperationGraph":
        """Builds the ComputationGraph from the nodes.

        This is done by:

        1. Building the structure graph.
        2. Building the computation graph by exploring the structure graph layers by
        layers in a breadth-first search.
        """
        operations = Operations()
        for node in nx.topological_sort(ctx.graph):
            if isinstance(node, FileObject):
                if node.encoding_format == EncodingFormat.GIT:
                    _add_operations_for_git(operations, node, ctx.folder)
                else:
                    _add_operations_for_file_object(operations, node, ctx.folder)
            elif isinstance(node, FileSet):
                if not node.contained_in:
                    _add_operations_for_local_file_sets(operations, node, ctx.folder)
            elif isinstance(node, RecordSet):
                _add_operations_for_record_set(
                    operations,
                    node,
                )
            elif isinstance(node, Field):
                _add_operations_for_field(operations, node)

        # Attach all entry nodes to a single `start` node
        entry_operations = operations.entry_operations()
        init_operation = InitOperation(operations=operations, node=metadata)
        for entry_operation in entry_operations:
            operations.add_edge(init_operation, entry_operation)
        return OperationGraph(issues=ctx.issues, operations=operations)

    def check_graph(self, ctx: Context):
        """Checks the operation graph for issues."""
        if not self.operations.is_directed():
            self.issues.add_error("Computation graph is not directed.")
        selfloops = [operation for operation, _ in nx.selfloop_edges(self.operations)]
        if selfloops:
            self.issues.add_error(
                f"The following operations refered to themselves: {selfloops}"
            )
        record_sets = [node for node in ctx.graph.nodes if isinstance(node, RecordSet)]
        for record_set in record_sets:
            record_set.check_joins_in_fields()
