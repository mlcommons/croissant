"""source_test module."""

import pytest
from rdflib.term import URIRef

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.structure_graph.nodes.source import Extract
from mlcroissant._src.structure_graph.nodes.source import FileProperty
from mlcroissant._src.structure_graph.nodes.source import is_file_property
from mlcroissant._src.structure_graph.nodes.source import Source
from mlcroissant._src.structure_graph.nodes.source import Transform
from mlcroissant._src.tests.nodes import assert_contain_error
from mlcroissant._src.tests.versions import parametrize_conforms_to


def test_source_bool():
    empty_source = Source(transforms=[Transform(replace="\\n/<eos>")])
    assert not empty_source

    whole_source = Source(field="one/two")
    assert whole_source


@pytest.mark.parametrize(
    ["conforms_to", "json_ld", "expected_source"],
    [
        [
            CroissantVersion.V_0_8,
            {
                "@id": "source",
                constants.SCHEMA_ORG_DISTRIBUTION: "my-csv",
                URIRef("http://mlcommons.org/schema/transform"): [
                    {URIRef("http://mlcommons.org/schema/replace"): "\\n/<eos>"},
                    {URIRef("http://mlcommons.org/schema/separator"): " "},
                ],
                URIRef("http://mlcommons.org/schema/extract"): {
                    URIRef("http://mlcommons.org/schema/column"): "my-column"
                },
            },
            Source(
                extract=Extract(column="my-column"),
                id="source",
                transforms=[Transform(replace="\\n/<eos>"), Transform(separator=" ")],
                distribution="my-csv",
            ),
        ],
        [
            CroissantVersion.V_1_0,
            {
                "@id": "source",
                URIRef("http://mlcommons.org/croissant/fileObject"): "my-csv",
                URIRef("http://mlcommons.org/croissant/transform"): [
                    {URIRef("http://mlcommons.org/croissant/replace"): "\\n/<eos>"},
                    {URIRef("http://mlcommons.org/croissant/separator"): " "},
                ],
                URIRef("http://mlcommons.org/croissant/extract"): {
                    URIRef("http://mlcommons.org/croissant/column"): "my-column"
                },
            },
            Source(
                extract=Extract(column="my-column"),
                id="source",
                transforms=[Transform(replace="\\n/<eos>"), Transform(separator=" ")],
                file_object="my-csv",
            ),
        ],
    ],
)
def test_source_parses_list(conforms_to, json_ld, expected_source):
    ctx = Context(conforms_to=conforms_to)
    expected_source.ctx = ctx
    assert Source.from_jsonld(ctx, json_ld) == expected_source
    assert not ctx.issues.errors
    assert not ctx.issues.warnings


@parametrize_conforms_to()
@pytest.mark.parametrize(
    ["jsonld", "expected_error"],
    [
        [
            "this is not a list",
            "Transform should be a dict with keys",
        ],
        [
            [{"not": "the right keys"}],
            "Transform should have one of the following properties",
        ],
    ],
)
def test_transformations_with_errors(conforms_to, jsonld, expected_error):
    ctx = Context(conforms_to=conforms_to)
    Transform.from_jsonld(ctx=ctx, jsonld=jsonld)
    assert len(ctx.issues.errors) == 1
    assert_contain_error(ctx.issues, expected_error)


@pytest.mark.parametrize(
    ["conforms_to", "json_ld"],
    [
        [
            CroissantVersion.V_0_8,
            {
                constants.SCHEMA_ORG_DISTRIBUTION: "my-csv",
                URIRef("http://mlcommons.org/schema/field"): "my-record-set/my-field",
            },
        ],
        [
            CroissantVersion.V_1_0,
            {
                URIRef("http://mlcommons.org/croissant/fileObject"): "my-csv",
                URIRef(
                    "http://mlcommons.org/croissant/field"
                ): "my-record-set/my-field",
            },
        ],
        [
            CroissantVersion.V_1_0,
            {
                URIRef("http://mlcommons.org/croissant/fileSet"): "my-csv",
                URIRef(
                    "http://mlcommons.org/croissant/field"
                ): "my-record-set/my-field",
            },
        ],
        [
            CroissantVersion.V_1_0,
            {
                URIRef("http://mlcommons.org/croissant/fileObject"): "my-csv",
                URIRef("http://mlcommons.org/croissant/fileSet"): "my-csv",
            },
        ],
    ],
)
def test_declaring_multiple_sources_in_one(conforms_to, json_ld):
    ctx = Context(conforms_to=conforms_to)
    Source.from_jsonld(ctx, json_ld)
    assert len(ctx.issues.errors) == 1
    assert_contain_error(ctx.issues, "Source should have one of the following properti")


@parametrize_conforms_to()
def test_declaring_multiple_data_extraction_in_one(conforms_to):
    ctx = Context(conforms_to=conforms_to)
    json_ld = {
        constants.ML_COMMONS_EXTRACT(ctx): {
            "@id": "jsonld-id",
            constants.ML_COMMONS_COLUMN(ctx): "csv_column",
            constants.ML_COMMONS_JSON_PATH(ctx): "json_path",
        },
    }
    assert Source.from_jsonld(ctx, json_ld) == Source(
        extract=Extract(column="csv_column", json_path="json_path"),
    )
    assert len(ctx.issues.errors) == 2
    assert_contain_error(
        ctx.issues, "Source should have one of the following properties"
    )


@parametrize_conforms_to()
def test_declaring_wrong_file_property(conforms_to):
    ctx = Context(conforms_to=conforms_to)
    json_ld = {
        constants.ML_COMMONS_EXTRACT(ctx): {
            constants.ML_COMMONS_FILE_PROPERTY(ctx): "foo",
        },
    }
    Source.from_jsonld(ctx, json_ld)
    assert_contain_error(
        ctx.issues,
        "fileProperty can only have values in"
        " `fullpath`, `filepath` and `content`. Got: foo",
    )


@pytest.mark.parametrize(
    ["source", "expected_column"],
    [
        [
            Source(file_object="my-csv", extract=Extract(column="my-csv-column")),
            "my-csv-column",
        ],
        [
            Source(
                file_object="my-csv",
                extract=Extract(file_property=FileProperty.content),
            ),
            FileProperty.content,
        ],
        [
            Source(
                file_object="my-csv",
                extract=Extract(json_path="/some/json/path"),
            ),
            "/some/json/path",
        ],
        [
            Source(field="record_set/field_name"),
            "record_set/field_name",
        ],
    ],
)
def test_get_field(source: Source, expected_column: str):
    assert source.get_column() == expected_column


def test_is_file_property():
    assert is_file_property("content")
    assert is_file_property("filename")
    assert is_file_property("filepath")
    assert is_file_property("fullpath")
    assert not is_file_property("foo")


def test_check_source_for_valid_json_path():
    issues = Issues()
    Source(id="id", extract=Extract(json_path="*.first.second")).check_source(
        issues.add_error
    )
    assert not issues.errors


def test_check_source_for_invalid_json_path():
    issues = Issues()
    Source(id="id", extract=Extract(json_path="invalid/json/path")).check_source(
        issues.add_error
    )
    errors = list(issues.errors)
    assert len(errors) == 1
    assert "Wrong JSONPath" in errors[0]
