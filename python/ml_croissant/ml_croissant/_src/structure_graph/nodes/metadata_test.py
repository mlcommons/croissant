"""Tests for Metadata."""

from unittest import mock

from etils import epath

from ml_croissant._src.core.issues import Context
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.nodes.metadata import Metadata
from ml_croissant._src.tests.nodes import create_test_node


def test_checks_are_performed():
    with mock.patch.object(
        Node, "assert_has_mandatory_properties"
    ) as mandatory_mock, mock.patch.object(
        Node, "assert_has_optional_properties"
    ) as optional_mock, mock.patch.object(
        Node, "validate_name"
    ) as validate_name_mock:
        create_test_node(Metadata, name="field_name")
        mandatory_mock.assert_called_once_with("name", "url")
        optional_mock.assert_called_once_with("citation", "license")
        validate_name_mock.assert_called_once()


def test_from_jsonld():
    issues = Issues()
    context = Context()
    folder = epath.Path("/foo/bar")
    jsonld = {
        "@type": "https://schema.org/Dataset",
        "https://schema.org/name": "foo",
        "https://schema.org/description": "bar",
        "https://schema.org/license": "License",
        "https://schema.org/url": "https://mlcommons.org",
    }
    assert Metadata.from_jsonld(issues, folder, jsonld) == Metadata(
        issues=issues,
        context=context,
        folder=folder,
        name="foo",
        description="bar",
        license="License",
        url="https://mlcommons.org",
    )
    assert not issues.errors
