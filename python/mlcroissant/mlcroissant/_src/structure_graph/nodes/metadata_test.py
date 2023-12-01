"""Tests for Metadata."""

from unittest import mock

from etils import epath
import pytest

from mlcroissant._src.core import constants
from mlcroissant._src.core.issues import Context
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.core.issues import ValidationError
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.metadata import Metadata
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet
from mlcroissant._src.tests.nodes import create_test_node


def test_checks_are_performed():
    with mock.patch.object(
        Node, "assert_has_mandatory_properties"
    ) as mandatory_mock, mock.patch.object(
        Node, "assert_has_optional_properties"
    ) as optional_mock, mock.patch.object(
        Node, "validate_name"
    ) as validate_name_mock:
        create_test_node(Metadata, name="field_name")
        mandatory_mock.assert_called_once_with("name")
        optional_mock.assert_called_once_with("citation", "license", "version")
        validate_name_mock.assert_called_once()


def test_from_jsonld():
    issues = Issues()
    context = Context()
    folder = epath.Path("/foo/bar")
    jsonld = {
        "@type": constants.SCHEMA_ORG_DATASET,
        constants.SCHEMA_ORG_NAME: "foo",
        constants.SCHEMA_ORG_DESCRIPTION: "bar",
        constants.SCHEMA_ORG_LICENSE: "License",
        constants.SCHEMA_ORG_URL: "https://mlcommons.org",
        constants.SCHEMA_ORG_VERSION: "1.0",
    }
    assert Metadata.from_jsonld(issues, folder, jsonld) == Metadata(
        issues=issues,
        context=context,
        folder=folder,
        name="foo",
        description="bar",
        license="License",
        url="https://mlcommons.org",
        version="1.0",
    )
    assert not issues.errors


def test_issues_in_metadata_are_shared_with_children():
    with pytest.raises(ValidationError, match="is mandatory, but does not exist"):
        Metadata(
            name="name",
            description="description",
            url="https://mlcommons.org",
            # We did not specify the RecordSet's name. Hence the exception above:
            record_sets=[RecordSet(description="description")],
        )
