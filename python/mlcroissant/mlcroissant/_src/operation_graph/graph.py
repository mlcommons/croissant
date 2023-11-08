"""graph module."""

import dataclasses

from etils import epath
import networkx as nx

from mlcroissant._src.core.constants import EncodingFormat
from mlcroissant._src.core.issues import Issues
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


def _add_operations_for_field_with_source(
    operations: Operations,
    node: Field,
):
    """Adds all operations for a node of type `Field`.

    Operations are:

    - `Join` if the field comes from several sources.
    - `ReadFields` to specify how the fields are read.
    """
    record_set = _find_record_set(node)
    operation = operations.last_operations(node, only_leaf=True)
    has_join = any(field for field in record_set.fields if field.references.uid)
    if has_join:
        operation = [operation >> Join(operations=operations, node=record_set)]
    (operation >> ReadFields(operations=operations, node=record_set))


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
    if node.contained_in:
        # Chain the operation from the predecessor
        operation = operations.last_operations(node, only_leaf=False)
    else:
        # Download the file
        operation = [Download(operations=operations, node=node)]
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
            operation = [operation >> Extract(operations=operations, node=node)]
        if isinstance(successor, FileSet):
            operation = [
                operation
                >> FilterFiles(operations=operations, node=successor)
                >> Concatenate(operations=operations, node=successor)
            ]
        if node.encoding_format and not should_extract(node.encoding_format):
            fields = tuple([
                field for field in node.successors if isinstance(field, Field)
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
                field for field in node.successors if isinstance(field, Field)
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
    fields = tuple([field for field in node.successors if isinstance(field, Field)])
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


@dataclasses.dataclass(frozen=True)
class OperationGraph:
    """Graph of dependent operations to execute to generate the dataset."""

    issues: Issues
    operations: Operations

    @classmethod
    def from_nodes(
        cls,
        issues: Issues,
        metadata: Node,
        graph: nx.DiGraph,
        folder: epath.Path,
    ) -> "OperationGraph":
        """Builds the ComputationGraph from the nodes.

        This is done by:

        1. Building the structure graph.
        2. Building the computation graph by exploring the structure graph layers by
        layers in a breadth-first search.
        """
        operations = Operations()
        # Find all fields
        for node in nx.topological_sort(graph):
            if isinstance(node, Field):
                parent = node.parent
                # TODO(https://github.com/mlcommons/croissant/issues/310): Change the
                # condition if isinstance(node, RecordSet). We don't need to iterate on
                # fields anymore as all fields are computed at the RecordSet level with
                # ReadFields.
                parent_has_data = isinstance(parent, RecordSet) and parent.data
                if node.source and not node.sub_fields and not parent_has_data:
                    _add_operations_for_field_with_source(
                        operations,
                        node,
                    )
            elif isinstance(node, RecordSet) and node.data:
                Data(operations=operations, node=node)
            elif isinstance(node, FileObject):
                if node.encoding_format == EncodingFormat.GIT:
                    _add_operations_for_git(operations, node, folder)
                else:
                    _add_operations_for_file_object(operations, node, folder)
            elif isinstance(node, FileSet):
                if not node.contained_in:
                    _add_operations_for_local_file_sets(operations, node, folder)

        # Attach all entry nodes to a single `start` node
        entry_operations = operations.entry_operations()
        init_operation = InitOperation(operations=operations, node=metadata)
        for entry_operation in entry_operations:
            operations.add_edge(init_operation, entry_operation)
        return OperationGraph(issues=issues, operations=operations)

    def check_graph(self):
        """Checks the operation graph for issues."""
        if not self.operations.is_directed():
            self.issues.add_error("Computation graph is not directed.")
        selfloops = [operation for operation, _ in nx.selfloop_edges(self.operations)]
        if selfloops:
            self.issues.add_error(
                f"The following operations refered to themselves: {selfloops}"
            )
