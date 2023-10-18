"""group_test module."""

from mlcroissant._src.operation_graph.operations import group
from mlcroissant._src.tests.nodes import empty_node
from mlcroissant._src.tests.operations import operations


def test_str_representation_start():
    operation = group.GroupRecordSetStart(operations=operations(), node=empty_node)
    assert str(operation) == "GroupRecordSetStart(node_name)"


def test_str_representation_end():
    operation = group.GroupRecordSetEnd(operations=operations(), node=empty_node)
    assert str(operation) == "GroupRecordSetEnd(node_name)"
