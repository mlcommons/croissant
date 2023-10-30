"""Tests for Fields."""

from unittest import mock

from rdflib import term

from mlcroissant._src.core.constants import DataType
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.tests.nodes import create_test_field
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


def test_data_type():
    # data_types can be a string:
    assert create_test_field(data_types=DataType.BOOL).data_types == [DataType.BOOL]
    # ...or a list of strings:
    assert create_test_field(
        data_types=[DataType.BOOL, "http://some-semantic-type"]
    ).data_types == [
        DataType.BOOL,
        term.URIRef("http://some-semantic-type"),
    ]

    # data_type are infered from the field...
    assert (
        create_test_field(
            data_types=[
                DataType.BOOL,
                "http://some-semantic-type",
            ]
        ).data_type
        is bool
    )
    # ...or from the predecessors. See the test case
    # `recordset_missing_context_for_datatype`.
