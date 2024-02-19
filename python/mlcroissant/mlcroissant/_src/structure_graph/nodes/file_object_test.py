"""Tests for FileObjects."""

from unittest import mock

from etils import epath
import pytest

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.file_object import FileObject
from mlcroissant._src.tests.nodes import create_test_node


def test_checks_are_performed():
    with mock.patch.object(
        Node, "assert_has_mandatory_properties"
    ) as mandatory_mock, mock.patch.object(
        Node, "assert_has_optional_properties"
    ), mock.patch.object(
        Node, "validate_name"
    ) as validate_name_mock, mock.patch.object(
        Node, "assert_has_exclusive_properties"
    ) as exclusive_mock:
        create_test_node(FileObject)
        mandatory_mock.assert_has_calls([
            mock.call("encoding_format", "name"), mock.call("content_url")
        ])
        exclusive_mock.assert_called_once_with(["md5", "sha256"])
        validate_name_mock.assert_called_once()


def test_checks_not_performed_for_live_dataset():
    with mock.patch.object(
        Node, "assert_has_mandatory_properties"
    ) as mandatory_mock, mock.patch.object(
        Node, "assert_has_optional_properties"
    ), mock.patch.object(
        Node, "validate_name"
    ) as validate_name_mock, mock.patch.object(
        Node, "assert_has_exclusive_properties"
    ) as exclusive_mock:
        ctx = Context(is_live_dataset=True)
        create_test_node(FileObject, ctx=ctx)
        mandatory_mock.assert_has_calls([
            mock.call("encoding_format", "name"), mock.call("content_url")
        ])
        exclusive_mock.assert_not_called()
        validate_name_mock.assert_called_once()


@pytest.mark.parametrize(
    ["encoding"],
    [
        ["text/csv"],
        ["text/tsv"],
    ],
)
def test_from_jsonld(encoding):
    ctx = Context()
    jsonld = {
        "@type": constants.SCHEMA_ORG_FILE_OBJECT(ctx),
        constants.SCHEMA_ORG_NAME: "foo",
        constants.SCHEMA_ORG_DESCRIPTION: "bar",
        constants.SCHEMA_ORG_CONTENT_URL: "https://mlcommons.org",
        constants.SCHEMA_ORG_ENCODING_FORMAT: encoding,
        constants.SCHEMA_ORG_SHA256: (
            "48a7c257f3c90b2a3e529ddd2cca8f4f1bd8e49ed244ef53927649504ac55354"
        ),
    }
    ctx.mapping = {"file1": epath.Path("~/Downloads/file1.csv")}
    file_object = FileObject.from_jsonld(ctx, jsonld)
    assert file_object.name == "foo"
    assert file_object.description == "bar"
    assert file_object.content_url == "https://mlcommons.org"
    assert file_object.encoding_format == encoding
    assert (
        file_object.sha256
        == "48a7c257f3c90b2a3e529ddd2cca8f4f1bd8e49ed244ef53927649504ac55354"
    )
    assert not ctx.issues.errors
