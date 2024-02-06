"""Tests for Metadata."""

from unittest import mock

import pytest

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.core.issues import ValidationError
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.metadata import Metadata
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet
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
        create_test_node(Metadata, name="field_name")
        mandatory_mock.assert_called_once_with("name")
        optional_mock.assert_called_once_with("cite_as", "license", "version")
        validate_name_mock.assert_called_once()


@parametrize_conforms_to()
def test_from_jsonld(conforms_to: CroissantVersion):
    ctx = Context(conforms_to=conforms_to)
    jsonld = {
        "@type": constants.SCHEMA_ORG_DATASET,
        constants.SCHEMA_ORG_NAME: "foo",
        constants.SCHEMA_ORG_DESCRIPTION: "bar",
        constants.DCTERMS_CONFORMS_TO: conforms_to.value,
        constants.SCHEMA_ORG_LICENSE: "License",
        constants.SCHEMA_ORG_URL: "https://mlcommons.org",
        constants.SCHEMA_ORG_VERSION: "1.0.0",
        constants.ML_COMMONS_DATA_BIASES(ctx): "data_biases",
        constants.ML_COMMONS_DATA_COLLECTION(ctx): "data_collection",
        constants.ML_COMMONS_PERSONAL_SENSITVE_INFORMATION(
            ctx
        ): "personal_sensitive_information",
    }
    assert Metadata.from_jsonld(ctx, jsonld) == Metadata(
        ctx=ctx,
        name="foo",
        description="bar",
        data_biases="data_biases",
        data_collection="data_collection",
        license="License",
        personal_sensitive_information="personal_sensitive_information",
        url="https://mlcommons.org",
        version="1.0.0",
    )
    assert not ctx.issues.errors


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
    ctx = Context()
    jsonld = {
        "@type": constants.SCHEMA_ORG_DATASET,
        constants.SCHEMA_ORG_NAME: "foo",
        constants.SCHEMA_ORG_DESCRIPTION: "bar",
        constants.SCHEMA_ORG_LICENSE: "License",
        constants.SCHEMA_ORG_URL: "https://mlcommons.org",
        constants.SCHEMA_ORG_VERSION: version,
    }
    with pytest.raises(ValidationError, match=rf"{expected_error}"):
        Metadata.from_jsonld(ctx, jsonld)


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
