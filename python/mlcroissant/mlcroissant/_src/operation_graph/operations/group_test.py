"""group_test module."""

from mlcroissant._src.operation_graph.operations import group
from mlcroissant._src.tests.nodes import empty_node
from mlcroissant._src.tests.operations import operations


def test_str_representation():
    operation = group.GroupRecordSet(operations=operations(), node=empty_node)
    assert str(operation) == "GroupRecordSet(node_name)"
