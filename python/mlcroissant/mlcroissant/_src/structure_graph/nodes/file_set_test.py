"""Tests for FileSets."""

from unittest import mock

from etils import epath

from mlcroissant._src.core import constants
from mlcroissant._src.core.issues import Context
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.file_set import FileSet
from mlcroissant._src.structure_graph.nodes.rdf import Rdf
from mlcroissant._src.tests.nodes import create_test_node


def test_checks_are_performed():
    with mock.patch.object(
        Node, "assert_has_mandatory_properties"
    ) as mandatory_mock, mock.patch.object(
        Node, "assert_has_optional_properties"
    ) as optional_mock, mock.patch.object(
        Node, "validate_name"
    ) as validate_name_mock:
        create_test_node(FileSet)
        mandatory_mock.assert_called_once_with("includes", "encoding_format", "name")
        optional_mock.assert_not_called()
        validate_name_mock.assert_called_once()


def test_from_jsonld():
    issues = Issues()
    context = Context()
    folder = epath.Path("/foo/bar")
    rdf = Rdf()
    jsonld = {
        "@type": constants.SCHEMA_ORG_FILE_SET,
        constants.SCHEMA_ORG_NAME: "foo",
        constants.SCHEMA_ORG_DESCRIPTION: "bar",
        constants.SCHEMA_ORG_CONTAINED_IN: "some.zip",
        constants.SCHEMA_ORG_ENCODING_FORMAT: "application/json",
        constants.ML_COMMONS_INCLUDES: "*.json",
    }
    assert FileSet.from_jsonld(issues, context, folder, rdf, jsonld) == FileSet(
        issues=issues,
        context=context,
        folder=folder,
        name="foo",
        description="bar",
        contained_in=["some.zip"],
        encoding_format="application/json",
        includes="*.json",
    )
    assert not issues.errors
