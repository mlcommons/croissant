"""Tests for Metadata."""

import copy
import datetime
from typing import Any
from unittest import mock

import pytest
from rdflib.namespace import SDO

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.core.issues import ValidationError
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.creative_work import CreativeWork
from mlcroissant._src.structure_graph.nodes.field import Field
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
        ctx = Context(conforms_to=CroissantVersion.V_0_8)
        create_test_node(Metadata, name="field_name", id="field_id", ctx=ctx)
        mandatory_mock.assert_called_once_with("name")
        optional_mock.assert_called_once_with(
            "cite_as", "date_published", "license", "version"
        )
        validate_name_mock.assert_called_once()


@parametrize_conforms_to()
@pytest.mark.parametrize("version", [1, 1.0, "1.0.0"])
def test_from_jsonld(conforms_to: CroissantVersion, version: Any):
    ctx = Context(conforms_to=conforms_to)
    jsonld = {
        "@type": constants.SCHEMA_ORG_DATASET,
        constants.SCHEMA_ORG_NAME: "foo",
        constants.SCHEMA_ORG_DESCRIPTION: "bar",
        constants.ML_COMMONS_CITE_AS(ctx): "bixtex: citation",
        constants.DCTERMS_CONFORMS_TO: conforms_to.value,
        # Dates can be datetimes...
        constants.SCHEMA_ORG_DATE_CREATED: "1990-02-01",
        # ...or dates can be string...
        constants.SCHEMA_ORG_DATE_MODIFIED: "1990-02-02",
        # ...or dates can be datetime.dates.
        constants.SCHEMA_ORG_DATE_PUBLISHED: "1990-02-03",
        constants.SCHEMA_ORG_LICENSE: [
            {
                "@type": SDO.CreativeWork,
                SDO.name: "U.S. Government Works",
                SDO.url: "https://www.usa.gov/government-works/",
            },
            "License",
        ],
        constants.SCHEMA_ORG_URL: "https://mlcommons.org",
        constants.SCHEMA_ORG_VERSION: version,
        constants.ML_COMMONS_IS_LIVE_DATASET(ctx): False,
    }
    metadata = Metadata.from_jsonld(ctx, jsonld)
    assert metadata.name == "foo"
    assert metadata.description == "bar"
    assert metadata.date_created == datetime.datetime(1990, 2, 1, 0, 0)
    assert metadata.date_modified == datetime.datetime(1990, 2, 2, 0, 0)
    assert metadata.date_published == datetime.datetime(1990, 2, 3, 0, 0)
    assert len(metadata.license) == 2
    assert isinstance(metadata.license[0], CreativeWork)
    assert metadata.license[0].name == "U.S. Government Works"
    assert metadata.license[0].url == "https://www.usa.gov/government-works/"
    assert metadata.license[1] == "License"
    assert metadata.ctx.is_live_dataset == False
    assert metadata.url == "https://mlcommons.org"
    assert metadata.version == "1.0.0"
    assert not ctx.issues.errors
    assert not ctx.issues.warnings


@pytest.mark.parametrize(
    ["version", "expected_error"],
    [
        [
            ["1.2.3"],
            "The version should be a string or a number. Got: <class 'list'>.",
        ],
    ],
)
def test_invalid_version(version, expected_error):
    ctx = Context()
    with pytest.raises(ValidationError, match=rf"{expected_error}"):
        Metadata(ctx, name="foo", version=version)


@pytest.mark.parametrize(
    ["version", "expected_warning"],
    [
        [
            "1.2.x",
            "Version doesn't follow MAJOR.MINOR.PATCH: 1.2.x.",
        ],
        [
            "...123",
            "Version doesn't follow MAJOR.MINOR.PATCH: ...123.",
        ],
        [
            "a.b.c",
            "Version doesn't follow MAJOR.MINOR.PATCH: a.b.c",
        ],
    ],
)
def test_warning_version(version, expected_warning):
    ctx = Context()
    metadata = Metadata(ctx, name="foo", version=version)
    assert any(expected_warning in warning for warning in metadata.ctx.issues.warnings)


@pytest.mark.parametrize(
    ["version", "expected_version"],
    [
        ["1", "1"],
        ["1.2", "1.2"],
        ["1.2.3", "1.2.3"],
        ["1.2.3-foo+bar", "1.2.3-foo+bar"],
        [1, "1.0.0"],
        [1.2, "1.2.0"],
        ["thisisanarbitraryversion", "thisisanarbitraryversion"],
    ],
)
def test_valid_version(version, expected_version):
    ctx = Context()
    metadata = Metadata(ctx, name="foo", version=version)
    assert metadata.version == expected_version


def test_issues_in_metadata_are_shared_with_children():
    with pytest.raises(ValidationError, match="is mandatory, but does not exist"):
        ctx = Context(conforms_to=CroissantVersion.V_0_8)
        Metadata(
            name="name",
            description="description",
            url="https://mlcommons.org",
            version="1.0.0",
            # We did not specify the RecordSet's name. Hence the exception above:
            record_sets=[
                RecordSet(id="record-set", description="description", ctx=ctx)
            ],
        )


def test_metadata_can_be_deep_copied():
    metadata = Metadata(name="foo")
    # PyTorch DataPipes requries copy.deepcopy:
    copied_metadata = copy.deepcopy(metadata)
    assert copied_metadata.name == metadata.name == "foo"
    assert copied_metadata is not metadata


def test_validate_license():
    # Disabling PyType in case someone doesn't use PyType.
    assert Metadata(name="foo").license is None
    assert Metadata(name="foo", license=None).license is None
    assert Metadata(name="foo", license="mit").license == [
        "mit"
    ]  # pytype: disable=wrong-arg-types
    assert Metadata(name="foo", license=["apache-2.0", "mit"]).license == [
        "apache-2.0",
        "mit",
    ]
    with pytest.raises(ValidationError, match="License should be a list of str"):
        Metadata(name="foo", license=42)  # pytype: disable=wrong-arg-types


def test_predecessors_are_propagated():
    field = Field(
        id="records/name",
        name="records/name",
        data_types=constants.DataType.TEXT,
    )
    record_set = RecordSet(
        id="records",
        fields=[field],
        data=[{"records/name": "train"}, {"records/name": "test"}],
    )
    Metadata(name="dummy", record_sets=[record_set])
    assert field.predecessors == {record_set}
