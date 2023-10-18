"""group_test module."""

from mlcroissant._src.operation_graph.operations import group
from mlcroissant._src.tests.nodes import empty_record_set
from mlcroissant._src.tests.operations import operations


def test_str_representation_start():
    operation = group.GroupRecordSetStart(
        operations=operations(), node=empty_record_set
    )
    assert str(operation) == "GroupRecordSetStart(record_set_name)"


def test_str_representation_end():
    operation = group.GroupRecordSetEnd(operations=operations(), node=empty_record_set)
    assert str(operation) == "GroupRecordSetEnd(record_set_name)"
