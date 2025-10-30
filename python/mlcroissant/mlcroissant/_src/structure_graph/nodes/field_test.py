"""Tests for Fields."""

import json
from unittest import mock

import pytest
from rdflib import term

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.source import Source
from mlcroissant._src.tests.nodes import create_test_field
from mlcroissant._src.tests.nodes import create_test_node


@pytest.mark.parametrize(
    ["conforms_to", "field_uuid"],
    [[CroissantVersion.V_0_8, "name"], [CroissantVersion.V_1_0, "id"]],
)
def test_checks_are_performed(conforms_to, field_uuid):
    with mock.patch.object(
        Node, "assert_has_mandatory_properties"
    ) as mandatory_mock, mock.patch.object(Node, "validate_name") as validate_name_mock:
        ctx = Context(conforms_to=conforms_to)
        create_test_node(Field, ctx=ctx)
        mandatory_mock.assert_called_once_with(field_uuid)
        validate_name_mock.assert_called_once()


@pytest.mark.parametrize(
    ["array_shape", "array_shape_tuple"], [["1,2,3", (1, 2, 3)], [None, (-1,)]]
)
def test_array_shape_tuple(array_shape, array_shape_tuple):
    field = create_test_field(is_array=True, array_shape=array_shape, value="constant")
    assert field.array_shape_tuple == array_shape_tuple


def test_data_type():
    # data_types can be a string:
    assert create_test_field(
        data_types=constants.DataType.BOOL, value="constant"
    ).data_types == [constants.DataType.BOOL]
    # ...or a list of strings:
    assert create_test_field(
        data_types=[constants.DataType.BOOL, "http://some-semantic-type"],
        value="constant",
    ).data_types == [
        constants.DataType.BOOL,
        term.URIRef("http://some-semantic-type"),
    ]

    # data_type are infered from the field...
    assert (
        create_test_field(
            data_types=[
                constants.DataType.BOOL,
                "http://some-semantic-type",
            ],
            value="constant",
        ).data_type
        is bool
    )
    # ...or from the predecessors. See the test case
    # `recordset_missing_context_for_datatype`.


def test_from_jsonld():
    ctx = Context()
    jsonld = {
        "@type": constants.ML_COMMONS_FIELD_TYPE(ctx),
        "@id": "foo_id",
        constants.SCHEMA_ORG_NAME: "foo",
        constants.SCHEMA_ORG_DESCRIPTION: "bar",
        constants.ML_COMMONS_DATA_TYPE(ctx): constants.DataType.BOOL,
        constants.SCHEMA_ORG_VALUE: "constant",
        constants.ML_COMMONS_ANNOTATION(ctx): {
            "@type": constants.ML_COMMONS_FIELD_TYPE(ctx),
            "@id": "annotation_id",
            constants.SCHEMA_ORG_NAME: "annotation",
            constants.SCHEMA_ORG_DESCRIPTION: "annotation description",
            constants.ML_COMMONS_DATA_TYPE(ctx): [
                constants.DataType.TEXT,
                constants.DataType.URL,
            ],
        },
    }
    field = Field.from_jsonld(ctx, jsonld)
    assert field.name == "foo"
    assert field.description == "bar"
    assert field.data_types == [constants.DataType.BOOL]
    assert field.value == "constant"
    assert len(field.annotations) == 1
    annotation = field.annotations[0]
    assert annotation.name == "annotation"
    assert annotation.description == "annotation description"
    assert set(annotation.data_types) == set([
        constants.DataType.TEXT, constants.DataType.URL
    ])


def test_value_atomic_to_json():
    """`value` should appear in compact JSON produced by to_json()."""
    ctx = Context()
    field = create_test_field(ctx=ctx, name="rating_scale", value="1-5 stars")
    out = field.to_json()
    assert out.get("value") == "1-5 stars"


def test_value_structured_from_jsonld():
    """Structured (object/array) constants should round-trip via from_jsonld."""
    ctx = Context()
    calib = {"offset": 3.2, "units": "mV", "curve": [1, 2, 3]}
    jld = {
        "@type": constants.ML_COMMONS_FIELD_TYPE(ctx),
        constants.SCHEMA_ORG_NAME: "sensor_calibration",
        constants.SCHEMA_ORG_VALUE: calib,
    }
    field = Field.from_jsonld(ctx, jld)
    assert field.name == "sensor_calibration"
    assert field.value == calib


def test_value_not_json_serializable():
    """Non-JSON values should surface a serialization error when exporting."""
    field = create_test_field(value={1, 2, 3})
    with pytest.raises(TypeError, match="set is not JSON serializable"):
        json.dumps(field.to_json())


def test_value_skips_source_validation():
    ctx = Context()
    with mock.patch.object(Source, "check_source") as mocked_check_source:
        Field(ctx=ctx, name="field", id="field", value="constant")
    mocked_check_source.assert_not_called()


def test_value_with_source_still_validates_source():
    ctx = Context()
    with mock.patch.object(Source, "check_source") as mocked_check_source:
        _ = Field(
            ctx=ctx,
            name="field",
            id="field",
            value="constant",
            source=Source(ctx=ctx, field="record_set/parent"),
        )
    mocked_check_source.assert_called_once()
    assert not ctx.issues.warnings
    errors = ctx.issues.errors
    assert len(errors) == 1
    error = next(iter(errors))
    assert "`source` and `value`" in error
