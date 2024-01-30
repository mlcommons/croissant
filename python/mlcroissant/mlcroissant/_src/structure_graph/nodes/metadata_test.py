"""Tests for Metadata."""

from unittest import mock

from etils import epath
import pytest

from mlcroissant._src.core import constants
from mlcroissant._src.core.issues import Context
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.core.issues import ValidationError
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.metadata import CroissantVersion
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
        constants.SCHEMA_ORG_VERSION: "1.0.0",
        constants.ML_COMMONS_DATA_BIASES: "data_biases",
        constants.ML_COMMONS_DATA_COLLECTION: "data_collection",
        constants.ML_COMMONS_PERSONAL_SENSITVE_INFORMATION: (
            "personal_sensitive_information"
        ),
    }
    assert Metadata.from_jsonld(issues, folder, jsonld) == Metadata(
        issues=issues,
        context=context,
        folder=folder,
        conforms_to=CroissantVersion.V_0_8,  # No version specified, so default to 0.8.
        name="foo",
        description="bar",
        data_biases="data_biases",
        data_collection="data_collection",
        license="License",
        personal_sensitive_information="personal_sensitive_information",
        url="https://mlcommons.org",
        version="1.0.0",
    )
    assert not issues.errors


@pytest.mark.parametrize(
    ["version", "expected_error"],
    [
        [
            "1.2.x",
            "Version doesn't follow MAJOR.MINOR.PATCH: 1.2.x.",
        ],
        [
            "1.2",
            "Version doesn't follow MAJOR.MINOR.PATCH: 1.2",
        ],
        [
            "a.b.c",
            "Version doesn't follow MAJOR.MINOR.PATCH: a.b.c",
        ],
        [
            1.2,
            "The version should be a string. Got: <class 'float'>.",
        ],
    ],
)
def test_validate_version(version, expected_error):
    issues = Issues()
    folder = epath.Path("/foo/bar")
    jsonld = {
        "@type": constants.SCHEMA_ORG_DATASET,
        constants.SCHEMA_ORG_NAME: "foo",
        constants.SCHEMA_ORG_DESCRIPTION: "bar",
        constants.SCHEMA_ORG_LICENSE: "License",
        constants.SCHEMA_ORG_URL: "https://mlcommons.org",
        constants.SCHEMA_ORG_VERSION: version,
    }
    with pytest.raises(ValidationError, match=rf"{expected_error}"):
        Metadata.from_jsonld(issues, folder, jsonld)


def test_issues_in_metadata_are_shared_with_children():
    with pytest.raises(ValidationError, match="is mandatory, but does not exist"):
        Metadata(
            name="name",
            description="description",
            url="https://mlcommons.org",
            version="1.0.0",
            # We did not specify the RecordSet's name. Hence the exception above:
            record_sets=[RecordSet(description="description")],
        )


@pytest.mark.parametrize(
    "conforms_to",
    [1, 1.0, "1.0"],
)
def test_conforms_to_is_invalid(conforms_to):
    metadata = Metadata(
        name="name",
        conforms_to=conforms_to,
    )
    assert any(
        error.startswith("conformsTo should be a string or a CroissantVersion.")
        for error in metadata.issues.errors
    )


@pytest.mark.parametrize(
    ["conforms_to", "expected"],
    [
        [None, CroissantVersion.V_0_8],
        ["http://mlcommons.org/croissant/0.8", CroissantVersion.V_0_8],
        ["http://mlcommons.org/croissant/1.0", CroissantVersion.V_1_0],
        [CroissantVersion.V_0_8, CroissantVersion.V_0_8],
        [CroissantVersion.V_1_0, CroissantVersion.V_1_0],
    ],
)
def test_conforms_to_is_checked(conforms_to, expected: CroissantVersion):
    # If left empty, conforms_to defaults to 0.8.
    metadata = Metadata(name="name", conforms_to=conforms_to)
    assert metadata.conforms_to == expected
