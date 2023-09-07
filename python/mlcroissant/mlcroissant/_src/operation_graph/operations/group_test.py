"""group_test module."""

from mlcroissant._src.operation_graph.operations import group
from mlcroissant._src.tests.nodes import empty_node


def test_str_representation():
    operation = group.GroupRecordSet(node=empty_node)
    assert str(operation) == "GroupRecordSet(node_name)"
