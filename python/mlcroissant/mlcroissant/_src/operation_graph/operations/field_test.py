"""field_test module."""

from mlcroissant._src.operation_graph.operations import field
from mlcroissant._src.tests.nodes import empty_field


def test_str_representation():
    operation = field.ReadField(node=empty_field)
    assert str(operation) == "ReadField(field_name)"
