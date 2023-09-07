"""Tests for RecordSets."""

from unittest import mock

from etils import epath
import pytest

from mlcroissant._src.core import constants
from mlcroissant._src.core.issues import Context
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.rdf import Rdf
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet
from mlcroissant._src.tests.nodes import create_test_field
from mlcroissant._src.tests.nodes import create_test_node
from mlcroissant._src.tests.nodes import create_test_record_set


@pytest.mark.parametrize(
    ["data", "error"],
    [
        [
            {"foo": "bar"},
            (
                "[record_set(record_set_name)] http://mlcommons.org/schema/data should"
                " declare a list. Got: <class 'dict'>."
            ),
        ],
        [
            [],
            (
                "[record_set(record_set_name)] http://mlcommons.org/schema/data should"
                " declare a non empty list."
            ),
        ],
        [
            [[{"foo": "bar"}]],
            (
                "[record_set(record_set_name)] http://mlcommons.org/schema/data should"
                " declare a list of dict. Got: a list of <class 'list'>."
            ),
        ],
        [
            [{"foo": "bar"}],
            (
                "[record_set(record_set_name)] Line #0 doesn't have the expected"
                " columns. Expected: {'field_name'}. Got: {'foo'}."
            ),
        ],
    ],
)
def test_invalid_data(data, error):
    issues = Issues()
    field = create_test_field(issues=issues)
    create_test_record_set(
        issues=issues,
        context=Context(record_set_name="record_set_name"),
        data=data,
        fields=[field],
    )
    assert error in issues.errors


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


def test_from_jsonld():
    issues = Issues()
    context = Context()
    folder = epath.Path("/foo/bar")
    rdf = Rdf()
    jsonld = {
        "@type": constants.ML_COMMONS_RECORD_SET_TYPE,
        constants.SCHEMA_ORG_NAME: "foo",
        constants.SCHEMA_ORG_DESCRIPTION: "bar",
        constants.ML_COMMONS_IS_ENUMERATION: True,
        constants.SCHEMA_ORG_KEY: ["key1", "key2"],
        constants.ML_COMMONS_DATA: [{"column1": ["value1", "value2"]}],
    }
    assert RecordSet.from_jsonld(issues, context, folder, rdf, jsonld) == RecordSet(
        issues=issues,
        context=context,
        folder=folder,
        name="foo",
        description="bar",
        is_enumeration=True,
        key=["key1", "key2"],
        data=[{"column1": ["value1", "value2"]}],
    )
    assert issues.errors == {
        "Line #0 doesn't have the expected columns. Expected: set(). Got: {'column1'}.",
        (
            "[record_set(foo)] Line #0 doesn't have the expected columns. Expected:"
            " set(). Got: {'column1'}."
        ),
    }
