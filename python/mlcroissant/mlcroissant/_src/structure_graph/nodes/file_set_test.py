"""Tests for FileSets."""

from unittest import mock

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.file_set import FileSet
from mlcroissant._src.tests.nodes import create_test_node
from mlcroissant._src.tests.versions import parametrize_conforms_to


def test_checks_are_performed():
    with mock.patch.object(
        Node, "assert_has_mandatory_properties"
    ) as mandatory_mock, mock.patch.object(
        Node, "assert_has_optional_properties"
    ) as optional_mock, mock.patch.object(
        Node, "validate_name"
    ) as validate_name_mock:
        create_test_node(FileSet)
        mandatory_mock.assert_called_once_with(
            "includes", "encoding_format", "name", "_uuid"
        )
        optional_mock.assert_not_called()
        validate_name_mock.assert_called_once()


@parametrize_conforms_to()
def test_from_jsonld(conforms_to):
    ctx = Context(conforms_to=conforms_to)
    if ctx.is_v0():
        contained_in = "some.zip"
    else:
        contained_in = {"@id": "some.zip"}
    jsonld = {
        "@type": constants.SCHEMA_ORG_FILE_SET(ctx),
        "@id": "foo_uuid",
        constants.SCHEMA_ORG_NAME: "foo",
        constants.SCHEMA_ORG_DESCRIPTION: "bar",
        constants.SCHEMA_ORG_CONTAINED_IN: contained_in,
        constants.SCHEMA_ORG_ENCODING_FORMAT: "application/json",
        constants.ML_COMMONS_EXCLUDES(ctx): "*.csv",
        constants.ML_COMMONS_INCLUDES(ctx): "*.json",
    }
    file_set = FileSet.from_jsonld(ctx, jsonld)
    assert file_set.name == "foo"
    assert file_set.description == "bar"
    assert file_set.contained_in == ["some.zip"]
    assert file_set.encoding_format == "application/json"
    assert file_set.excludes == ["*.csv"]
    assert file_set.includes == ["*.json"]
    assert not ctx.issues.errors
