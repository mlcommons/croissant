"""Tests for RecordSets."""

from unittest import mock

import pytest

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet
from mlcroissant._src.tests.nodes import create_test_field
from mlcroissant._src.tests.nodes import create_test_node
from mlcroissant._src.tests.nodes import create_test_record_set
from mlcroissant._src.tests.versions import parametrize_conforms_to


@pytest.mark.parametrize(
    ["data", "error"],
    [
        [
            {"foo": "bar"},
            (
                "[RecordSet(record_set_name)] http://mlcommons.org/croissant/data"
                " should declare a list. Got: <class 'dict'>."
            ),
        ],
        [
            [],
            (
                "[RecordSet(record_set_name)] http://mlcommons.org/croissant/data"
                " should declare a non empty list."
            ),
        ],
        [
            [[{"foo": "bar"}]],
            (
                "[RecordSet(record_set_name)] http://mlcommons.org/croissant/data"
                " should declare a list of dict. Got: a list of <class 'list'>."
            ),
        ],
        [
            [{"foo": "bar"}],
            (
                "[RecordSet(record_set_name)] Line #0 doesn't have the expected"
                " columns. Expected: {'field_name'}. Got: {'foo'}."
            ),
        ],
    ],
)
def test_invalid_data(data, error):
    ctx = Context()
    field = create_test_field(ctx=ctx)
    create_test_record_set(
        ctx=ctx,
        data=data,
        fields=[field],
    )
    assert error in ctx.issues.errors


def test_checks_are_performed():
    with mock.patch.object(
        Node, "assert_has_mandatory_properties"
    ) as mandatory_mock, mock.patch.object(
        Node, "assert_has_optional_properties"
    ) as optional_mock, mock.patch.object(
        Node, "validate_name"
    ) as validate_name_mock:
        create_test_node(RecordSet)
        mandatory_mock.assert_called_once_with("name")
        optional_mock.assert_called_once_with("description")
        validate_name_mock.assert_called_once()


@parametrize_conforms_to()
def test_from_jsonld(conforms_to: CroissantVersion):
    ctx = Context(conforms_to=conforms_to)
    jsonld = {
        "@type": constants.ML_COMMONS_RECORD_SET_TYPE(ctx),
        constants.SCHEMA_ORG_NAME: "foo",
        constants.SCHEMA_ORG_DESCRIPTION: "bar",
        constants.ML_COMMONS_IS_ENUMERATION(ctx): True,
        constants.SCHEMA_ORG_KEY(ctx): ["key1", "key2"],
        constants.ML_COMMONS_DATA(ctx): [{"column1": ["value1", "value2"]}],
    }
    assert RecordSet.from_jsonld(ctx, jsonld) == RecordSet(
        ctx=ctx,
        name="foo",
        description="bar",
        is_enumeration=True,
        key=["key1", "key2"],
        data=[{"column1": ["value1", "value2"]}],
    )
    assert ctx.issues.errors == {
        (
            "[RecordSet(foo)] Line #0 doesn't have the expected columns. Expected:"
            " set(). Got: {'column1'}."
        ),
        (
            "[RecordSet(foo)] Line #0 doesn't have the expected columns. Expected:"
            " set(). Got: {'column1'}."
        ),
    }
