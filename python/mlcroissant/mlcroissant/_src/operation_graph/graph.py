"""graph module."""

import dataclasses

from etils import epath
import networkx as nx

from mlcroissant._src.core import constants
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.operation_graph.base_operation import Operation
from mlcroissant._src.operation_graph.operations import Concatenate
from mlcroissant._src.operation_graph.operations import Data
from mlcroissant._src.operation_graph.operations import Download
from mlcroissant._src.operation_graph.operations import Extract
from mlcroissant._src.operation_graph.operations import FilterFiles
from mlcroissant._src.operation_graph.operations import GroupRecordSetEnd
from mlcroissant._src.operation_graph.operations import GroupRecordSetStart
from mlcroissant._src.operation_graph.operations import InitOperation
from mlcroissant._src.operation_graph.operations import Join
from mlcroissant._src.operation_graph.operations import LocalDirectory
from mlcroissant._src.operation_graph.operations import Read
from mlcroissant._src.operation_graph.operations import ReadField
from mlcroissant._src.operation_graph.operations.extract import should_extract
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.graph import get_entry_nodes
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.file_object import FileObject
from mlcroissant._src.structure_graph.nodes.file_set import FileSet
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet

LastOperation = dict[Node, Operation]


def _find_record_set(node: Node) -> RecordSet:
    """Finds the record set to which a field is attached.

    The record set will be typically either the parent or the parent's parent.
    """
    for parent in reversed(node.parents):
        if isinstance(parent, RecordSet):
            return parent
    raise ValueError(f"Node {node} has no RecordSet parent.")


def _add_operations_for_field_with_source(
    operations: nx.DiGraph,
    last_operation: LastOperation,
    node: Field,
):
    """Adds all operations for a node of type `Field`.

    Operations are:

    - `Join` if the field comes from several sources.
    - `ReadField` to specify how the field is read.
    - `GroupRecordSetStart` to structure the final dict that is sent back to the user.
    """
    # Attach the field to a record set
    record_set = _find_record_set(node)
    group_record_set = GroupRecordSetStart(operations=operations, node=record_set)
    join = Join(operations=operations, node=record_set)
    operations.add_node(join)
    operations.add_edge(join, group_record_set)
    for predecessor in node.predecessors:
        operations.add_edge(last_operation[predecessor], join)
    if not node.source:
        node.add_error("Wrong source for the node")
        return
    # Read/extract the field
    read_field = ReadField(operations=operations, node=node)
    operations.add_edge(group_record_set, read_field)
    end_group_record_set = GroupRecordSetEnd(operations=operations, node=record_set)
    operations.add_edge(read_field, end_group_record_set)
    last_operation[node] = end_group_record_set


def _add_operations_for_record_set_with_data(
    operations: nx.DiGraph,
    last_operation: LastOperation,
    node: RecordSet,
):
    """Adds a `Data` operation for a node of type `RecordSet` with data.

    Those nodes return a DataFrame representing the lines in `data`.
    """
    operation = Data(operations=operations, node=node)
    last_operation[node] = operation


def _add_operations_for_file_object(
    graph: nx.MultiDiGraph,
    operations: nx.DiGraph,
    last_operation: LastOperation,
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
    for successor in graph.successors(node):
        if node.contained_in:
            # Chain the operation from the rpedecessor
            operation = last_operation[node]
        else:
            # Download the file
            operation = Download(operations=operations, node=node)
            operations.add_node(operation)
        # Extract the file if needed
        if (
            should_extract(node.encoding_format)
            and isinstance(successor, (FileObject, FileSet))
            and not should_extract(successor.encoding_format)
        ):
            extract = Extract(operations=operations, node=node)
            operations.add_edge(operation, extract)
            operation = extract
        if isinstance(successor, FileSet):
            filter = FilterFiles(operations=operations, node=successor)
            operations.add_edge(extract, filter)
            last_operation[node] = filter
            operation = filter
            concatenate = Concatenate(operations=operations, node=successor)
            operations.add_edge(operation, concatenate)
            operation = concatenate
        last_operation[successor] = operation
    if not should_extract(node.encoding_format):
        read = Read(
            operations=operations,
            node=node,
            folder=folder,
            fields=graph.successors(node),
        )
        operations.add_edge(operation, read)
        operation = read
    last_operation[node] = operation


def _add_operations_for_git(
    graph: nx.MultiDiGraph,
    operations: nx.DiGraph,
    last_operation: LastOperation,
    node: FileObject,
    folder: epath.Path,
):
    """Adds all operations for a FileObject reading from a Git repository."""
    operation = Download(operations=operations, node=node)
    operations.add_node(operation)
    for successor in graph.successors(node):
        if isinstance(successor, FileSet):
            filter = FilterFiles(operations=operations, node=successor)
            operations.add_edge(operation, filter)
            read = Read(
                operations=operations,
                node=successor,
                folder=folder,
                fields=graph.successors(node),
            )
            operations.add_edge(filter, read)
            operation = read
    last_operation[node] = operation


def _add_operations_for_local_file_sets(
    graph: nx.MultiDiGraph,
    operations: nx.DiGraph,
    last_operation: LastOperation,
    node: FileSet,
    folder: epath.Path,
):
    """Adds all operations for a FileSet reading from local files."""
    directory = LocalDirectory(
        operations=operations,
        node=node,
        folder=folder,
    )
    operations.add_node(directory)

    filter_files = FilterFiles(operations=operations, node=node)
    operations.add_node(filter_files)
    operations.add_edge(directory, filter_files)

    read = Read(
        operations=operations,
        node=node,
        folder=folder,
        fields=graph.successors(node),
    )
    operations.add_node(read)
    operations.add_edge(filter_files, read)
    last_operation[node] = read


@dataclasses.dataclass(frozen=True)
class OperationGraph:
    """Graph of dependent operations to execute to generate the dataset."""

    issues: Issues
    operations: nx.DiGraph

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
        last_operation: LastOperation = {}
        operations = nx.DiGraph()
        # Find all fields
        for node in nx.topological_sort(graph):
            predecessors = graph.predecessors(node)
            # Transfer operation from predecessor -> node.
            for predecessor in predecessors:
                if predecessor in last_operation and node not in last_operation:
                    last_operation[node] = last_operation[predecessor]
            if isinstance(node, Field):
                parent = node.parent
                parent_has_data = isinstance(parent, RecordSet) and parent.data
                if node.source and not node.sub_fields and not parent_has_data:
                    _add_operations_for_field_with_source(
                        operations,
                        last_operation,
                        node,
                    )
            elif isinstance(node, RecordSet) and node.data:
                _add_operations_for_record_set_with_data(
                    operations,
                    last_operation,
                    node,
                )
            elif isinstance(node, FileObject):
                if node.encoding_format == constants.GIT_HTTPS_ENCODING_FORMAT:
                    _add_operations_for_git(
                        graph, operations, last_operation, node, folder
                    )
                else:
                    _add_operations_for_file_object(
                        graph, operations, last_operation, node, folder
                    )
            elif isinstance(node, FileSet):
                if not node.contained_in:
                    _add_operations_for_local_file_sets(
                        graph, operations, last_operation, node, folder
                    )

        # Attach all entry nodes to a single `start` node
        entry_operations = get_entry_nodes(operations)
        init_operation = InitOperation(operations=operations, node=metadata)
        for entry_operation in entry_operations:
            operations.add_edge(init_operation, entry_operation)
        return OperationGraph(issues=issues, operations=operations)

    def check_graph(self):
        """Checks the computation graph for issues."""
        if not self.operations.is_directed():
            self.issues.add_error("Computation graph is not directed.")
        selfloops = [
            operation.uid for operation, _ in nx.selfloop_edges(self.operations)
        ]
        if selfloops:
            self.issues.add_error(
                f"The following operations refered to themselves: {selfloops}"
            )
