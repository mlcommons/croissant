"""Tests for Fields."""

from unittest import mock

import pytest
from rdflib import term

from mlcroissant._src.core.constants import DataType
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.tests.nodes import create_test_field
from mlcroissant._src.tests.nodes import create_test_node


@pytest.mark.parametrize(
    ["conforms_to", "field_uuid"],
    [[CroissantVersion.V_0_8, "name"], [CroissantVersion.V_1_0, "id"]],
)
def test_checks_are_performed(conforms_to, field_uuid):
    with mock.patch.object(
        Node, "assert_has_mandatory_properties"
    ) as mandatory_mock, mock.patch.object(Node, "validate_name") as validate_name_mock:
        ctx = Context(conforms_to=conforms_to)
        create_test_node(Field, ctx=ctx)
        mandatory_mock.assert_called_once_with(field_uuid)
        validate_name_mock.assert_called_once()


@pytest.mark.parametrize(
    ["array_shape", "array_shape_tuple"], [["1,2,3", (1, 2, 3)], [None, (-1,)]]
)
def test_array_shape_tuple(array_shape, array_shape_tuple):
    field = create_test_field(is_array=True, array_shape=array_shape)
    assert field.array_shape_tuple == array_shape_tuple


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
