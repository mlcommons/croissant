"""source_test module."""

import pytest
from rdflib.term import URIRef

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.structure_graph.nodes.source import Extract
from mlcroissant._src.structure_graph.nodes.source import FileProperty
from mlcroissant._src.structure_graph.nodes.source import get_parent_uid
from mlcroissant._src.structure_graph.nodes.source import is_file_property
from mlcroissant._src.structure_graph.nodes.source import Source
from mlcroissant._src.structure_graph.nodes.source import Transform
from mlcroissant._src.tests.versions import parametrize_conforms_to


def test_source_bool():
    empty_source = Source(transforms=[Transform(replace="\\n/<eos>")])
    assert not empty_source

    whole_source = Source(uid="one/two")
    assert whole_source


for ctx in [Context(conforms_to=conforms_to) for conforms_to in CroissantVersion]:

    @pytest.mark.parametrize(
        ["json_ld", "expected_source"],
        [
            [
                {
                    constants.ML_COMMONS_FIELD(ctx): "token-files/content",
                },
                Source(uid="token-files/content", node_type="field"),
            ],
            [
                {
                    constants.ML_COMMONS_FIELD(ctx): "token-files/content",
                    constants.ML_COMMONS_TRANSFORM(ctx): [
                        {constants.ML_COMMONS_REPLACE(ctx): "\\n/<eos>"},
                        {constants.ML_COMMONS_SEPARATOR(ctx): " "},
                    ],
                },
                Source(
                    uid="token-files/content",
                    transforms=[
                        Transform(replace="\\n/<eos>"),
                        Transform(separator=" "),
                    ],
                    node_type="field",
                ),
            ],
            [
                [
                    {
                        constants.ML_COMMONS_FIELD(ctx): "token-files/content",
                        constants.ML_COMMONS_TRANSFORM(ctx): [
                            {constants.ML_COMMONS_REPLACE(ctx): "\\n/<eos>"},
                            {constants.ML_COMMONS_SEPARATOR(ctx): " "},
                        ],
                    }
                ],
                Source(
                    uid="token-files/content",
                    transforms=[
                        Transform(replace="\\n/<eos>"),
                        Transform(separator=" "),
                    ],
                    node_type="field",
                ),
            ],
        ],
    )
    def test_source_parses_list(json_ld, expected_source):
        assert Source.from_jsonld(ctx, json_ld) == expected_source
        assert not ctx.issues.errors
        assert not ctx.issues.warnings


@pytest.mark.parametrize(
    ["conforms_to", "json_ld", "expected_source"],
    [
        [
            CroissantVersion.V_0_8,
            {
                constants.SCHEMA_ORG_DISTRIBUTION: "my-csv",
                URIRef("http://mlcommons.org/schema/transform"): [
                    {
                        URIRef("http://mlcommons.org/schema/replace"): "\\n/<eos>",
                        URIRef("http://mlcommons.org/schema/separator"): " ",
                    }
                ],
                URIRef("http://mlcommons.org/schema/extract"): {
                    URIRef("http://mlcommons.org/schema/column"): "my-column"
                },
            },
            Source(
                extract=Extract(column="my-column"),
                uid="my-csv",
                transforms=[Transform(replace="\\n/<eos>", separator=" ")],
                node_type="distribution",
            ),
        ],
        [
            CroissantVersion.V_1_0,
            {
                URIRef("http://mlcommons.org/croissant/fileObject"): "my-csv",
                URIRef("http://mlcommons.org/croissant/transform"): [
                    {
                        URIRef("http://mlcommons.org/croissant/replace"): "\\n/<eos>",
                        URIRef("http://mlcommons.org/croissant/separator"): " ",
                    }
                ],
                URIRef("http://mlcommons.org/croissant/extract"): {
                    URIRef("http://mlcommons.org/croissant/column"): "my-column"
                },
            },
            Source(
                extract=Extract(column="my-column"),
                uid="my-csv",
                transforms=[Transform(replace="\\n/<eos>", separator=" ")],
                node_type="fileObject",
            ),
        ],
    ],
)
def test_source_parses_list_with_node_type(conforms_to, json_ld, expected_source):
    ctx = Context(conforms_to=conforms_to)
    assert Source.from_jsonld(ctx, json_ld) == expected_source
    assert not ctx.issues.errors
    assert not ctx.issues.warnings


@parametrize_conforms_to()
@pytest.mark.parametrize(
    ["jsonld", "expected_error"],
    [
        [
            "this is not a list",
            'Transform "this is not a list" should be a dict with the keys',
        ],
        [
            [{"not": "the right keys"}],
            (
                "Transform \"{'not': 'the right keys'}\" should be a dict with at"
                " least one key in"
            ),
        ],
    ],
)
def test_transformations_with_errors(conforms_to, jsonld, expected_error):
    ctx = Context(conforms_to=conforms_to)
    Transform.from_jsonld(ctx=ctx, jsonld=jsonld)
    assert len(ctx.issues.errors) == 1
    assert expected_error in list(ctx.issues.errors)[0]


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
    assert Source.from_jsonld(ctx, json_ld) == Source()
    assert len(ctx.issues.errors) == 1
    assert "source should declare either" in list(ctx.issues.errors)[0]


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
    assert any(
        "extract should have one of the following properties" in error
        for error in list(ctx.issues.errors)
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
    assert any(
        "fileProperty can only have values in"
        " `fullpath`, `filepath` and `content`. Got: foo"
        in error
        for error in ctx.issues.errors
    )


@pytest.mark.parametrize(
    ["source", "expected_column"],
    [
        [
            Source(uid="my-csv", extract=Extract(column="my-csv-column")),
            "my-csv-column",
        ],
        [
            Source(
                uid="my-csv",
                extract=Extract(file_property=FileProperty.content),
            ),
            FileProperty.content,
        ],
        [
            Source(
                uid="my-csv",
                extract=Extract(json_path="/some/json/path"),
            ),
            "/some/json/path",
        ],
        [
            Source(uid="record_set/field_name"),
            "field_name",
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
    Source(uid="uid", extract=Extract(json_path="*.first.second")).check_source(
        issues.add_error
    )
    assert not issues.errors


def test_check_source_for_invalid_json_path():
    issues = Issues()
    Source(uid="uid", extract=Extract(json_path="invalid/json/path")).check_source(
        issues.add_error
    )
    errors = list(issues.errors)
    assert len(errors) == 1
    assert "Wrong JSONPath" in errors[0]


def test_get_parent_uid():
    assert get_parent_uid("foo") == "foo"
    assert get_parent_uid("foo/bar") == "foo"
    assert get_parent_uid("foo/bar/baz") == "foo"
