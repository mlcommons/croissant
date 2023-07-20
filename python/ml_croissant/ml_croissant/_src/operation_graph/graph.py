"""graph module."""

import dataclasses

from etils import epath
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.nodes import (
    Field,
    FileObject,
    FileSet,
    RecordSet,
)
from ml_croissant._src.operation_graph.base_operation import Operation
from ml_croissant._src.operation_graph.operations import (
    Concatenate,
    Data,
    Download,
    Extract,
    GroupRecordSet,
    InitOperation,
    Join,
    ParseJson,
    Read,
    ReadField,
)
from ml_croissant._src.operation_graph.operations.extract import should_extract
from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.graph import get_entry_nodes
import networkx as nx

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
    graph: nx.MultiDiGraph,
    operations: nx.MultiDiGraph,
    last_operation: LastOperation,
    node: Field,
):
    """Adds all operations for a node of type `Field`.

    Operations are:

    - `Join` if the field comes from several sources.
    - `ReadField` to specify how the field is read.
    - `GroupRecordSet` to structure the final dict that is sent back to the user.
    """
    # Attach the field to a record set
    record_set = _find_record_set(node)
    group_record_set = GroupRecordSet(node=record_set)
    join = Join(node=record_set)
    # `Join()` takes left=Source and right=Source as kwargs.
    if node.references.uid:
        kwargs = {
            "left": node.source,
            "right": node.references,
        }
        operations.add_node(join, kwargs=kwargs)
    else:
        # Else, we add a dummy JOIN operation.
        operations.add_node(join)
    # Parse JSON if necessary.
    if node.source.extract.json_path:
        parse_json = ParseJson(node=record_set)
        if parse_json in operations:
            kwargs = operations[parse_json].get("kwargs")
        else:
            kwargs = {"fields": []}
        kwargs["fields"].append(node)
        operations.add_node(parse_json, kwargs=kwargs)
        operations.add_edge(join, parse_json)
        operations.add_edge(parse_json, group_record_set)
    else:
        operations.add_edge(join, group_record_set)
    for predecessor in graph.predecessors(node):
        operations.add_edge(last_operation[predecessor], join)
    if not node.source:
        node.add_error("Wrong source for the node")
        return
    # Read/extract the field
    read_field = ReadField(node=node)
    operations.add_edge(group_record_set, read_field)
    last_operation[node] = read_field


def _add_operations_for_record_set_with_data(
    last_operation: LastOperation,
    node: RecordSet,
):
    """Adds a `Data` operation for a node of type `RecordSet` with data.

    Those nodes return a DataFrame representing the lines in `data`.
    """
    operation = Data(node=node)
    last_operation[node] = operation


def _add_operations_for_file_object(
    graph: nx.MultiDiGraph,
    operations: nx.MultiDiGraph,
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
    # Download the file
    operation = Download(node=node, url=node.content_url)
    operations.add_node(operation)
    for successor in graph.successors(node):
        # Extract the file if needed
        if (
            should_extract(node.encoding_format)
            and isinstance(successor, FileSet)
            and not should_extract(successor.encoding_format)
        ):
            extract = Extract(node=node, target_node=successor)
            operations.add_edge(operation, extract)
            last_operation[node] = extract
            operation = extract
        if isinstance(successor, FileSet):
            concatenate = Concatenate(node=successor)
            operations.add_edge(operation, concatenate)
            operation = concatenate
    if not should_extract(node.encoding_format):
        read = Read(
            node=node,
            url=node.content_url,
            folder=folder,
        )
        operations.add_edge(operation, read)
        operation = read
    last_operation[node] = operation


@dataclasses.dataclass(frozen=True)
class OperationGraph:
    """Graph of dependent operations to execute to generate the dataset."""

    issues: Issues
    operations: nx.MultiDiGraph

    @classmethod
    def from_nodes(
        cls,
        issues: Issues,
        metadata: Node,
        graph: nx.MultiDiGraph,
        folder: epath.Path,
    ) -> "OperationGraph":
        """Builds the ComputationGraph from the nodes.

        This is done by:

        1. Building the structure graph.
        2. Building the computation graph by exploring the structure graph layers by
        layers in a breadth-first search.
        """
        last_operation: LastOperation = {}
        operations = nx.MultiDiGraph()
        # Find all fields
        for node in nx.topological_sort(graph):
            predecessors = graph.predecessors(node)
            # Transfer operation from predecessor -> node.
            for predecessor in predecessors:
                if predecessor in last_operation:
                    last_operation[node] = last_operation[predecessor]
            if isinstance(node, Field):
                if node.source and not node.has_sub_fields and not node.data:
                    _add_operations_for_field_with_source(
                        graph,
                        operations,
                        last_operation,
                        node,
                    )
            elif isinstance(node, RecordSet) and node.data:
                _add_operations_for_record_set_with_data(
                    last_operation,
                    node,
                )
            elif isinstance(node, FileObject):
                _add_operations_for_file_object(
                    graph, operations, last_operation, node, folder
                )

        # Attach all entry nodes to a single `start` node
        entry_operations = get_entry_nodes(operations)
        init_operation = InitOperation(node=metadata)
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
