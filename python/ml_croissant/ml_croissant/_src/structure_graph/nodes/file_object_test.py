"""Tests for FileObjects."""

from unittest import mock

from etils import epath

from ml_croissant._src.core.issues import Context
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.nodes.file_object import FileObject
from ml_croissant._src.tests.nodes import create_test_node


def test_checks_are_performed():
    with mock.patch.object(
        Node, "assert_has_mandatory_properties"
    ) as mandatory_mock, mock.patch.object(
        Node, "assert_has_optional_properties"
    ) as optional_mock, mock.patch.object(
        Node, "validate_name"
    ) as validate_name_mock, mock.patch.object(
        Node, "assert_has_exclusive_properties"
    ) as exclusive_mock:
        create_test_node(FileObject)
        mandatory_mock.assert_called_once_with("content_url", "encoding_format", "name")
        optional_mock.assert_not_called()
        exclusive_mock.assert_called_once_with(["md5", "sha256"])
        validate_name_mock.assert_called_once()


def test_from_jsonld():
    issues = Issues()
    context = Context()
    folder = epath.Path("/foo/bar")
    jsonld = {
        "@type": "https://schema.org/FileObject",
        "https://schema.org/name": "foo",
        "https://schema.org/description": "bar",
        "https://schema.org/contentUrl": "https://mlcommons.org",
        "https://schema.org/encodingFormat": "text/csv",
        "https://schema.org/sha256": (
            "48a7c257f3c90b2a3e529ddd2cca8f4f1bd8e49ed244ef53927649504ac55354"
        ),
    }
    assert FileObject.from_jsonld(issues, context, folder, jsonld) == FileObject(
        issues=issues,
        context=context,
        folder=folder,
        name="foo",
        description="bar",
        content_url="https://mlcommons.org",
        encoding_format="text/csv",
        sha256="48a7c257f3c90b2a3e529ddd2cca8f4f1bd8e49ed244ef53927649504ac55354",
    )
    assert not issues.errors
