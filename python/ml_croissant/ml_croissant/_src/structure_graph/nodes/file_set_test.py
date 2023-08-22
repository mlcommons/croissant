"""Tests for FileSets."""

from unittest import mock

from etils import epath

from ml_croissant._src.core.issues import Context
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.nodes.file_set import FileSet
from ml_croissant._src.tests.nodes import create_test_node


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
    jsonld = {
        "@type": "https://schema.org/FileSet",
        "https://schema.org/name": "foo",
        "https://schema.org/description": "bar",
        "https://schema.org/containedIn": "some.zip",
        "https://schema.org/encodingFormat": "application/json",
        "http://mlcommons.org/schema/includes": "*.json",
    }
    assert FileSet.from_jsonld(issues, context, folder, jsonld) == FileSet(
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
