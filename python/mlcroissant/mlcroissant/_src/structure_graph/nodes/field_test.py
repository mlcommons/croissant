"""Tests for Fields."""

from unittest import mock

from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.tests.nodes import create_test_node


def test_checks_are_performed():
    with mock.patch.object(
        Node, "assert_has_mandatory_properties"
    ) as mandatory_mock, mock.patch.object(
        Node, "assert_has_optional_properties"
    ) as optional_mock, mock.patch.object(
        Node, "validate_name"
    ) as validate_name_mock:
        create_test_node(Field)
        mandatory_mock.assert_called_once_with("name")
        optional_mock.assert_called_once_with("description")
        validate_name_mock.assert_called_once()
