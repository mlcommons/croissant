"""graph_test module."""

from typing import Any

from ml_croissant._src.core.issues import Context, Issues
from ml_croissant._src.structure_graph.graph import (
    from_json_to_jsonld,
    from_jsonld_to_nodes,
    Json,
    JsonLd,
)
from ml_croissant._src.structure_graph.nodes import (
    FileObject,
    Metadata,
)


def _remove_keys(json: Json | JsonLd, keys: list[str]) -> Any:
    """Edits a dict in place by removing the `keys` recursively."""
    if isinstance(json, dict):
        for key, value in json.copy().items():
            if key in keys:
                del json[key]
            elif isinstance(value, (dict, list)):
                json[key] = _remove_keys(json[key], keys)
    elif isinstance(json, list):
        return [_remove_keys(element, keys) for element in json]
    return json


def assert_jsons_are_equal(json1: JsonLd, json2: JsonLd, ignore_keys: list[str] = []):
    """Asserts two JSONs are equal by ignoring some keys."""
    _remove_keys(json1, ignore_keys)
    _remove_keys(json2, ignore_keys)
    assert json1 == json2


def test_remove_keys():
    json = {"foo": "foo", "bar": [{"foo": "foo", "bar": "bar"}]}
    _remove_keys(json, ["foo"])
    assert json == {"bar": [{"bar": "bar"}]}


def test_from_json_to_jsonld():
    json = {
        "@context": {
            "@vocab": "https://schema.org/",
            "sc": "https://schema.org/",
            "ml": "http://mlcommons.org/schema/",
            "includes": "ml:includes",
            "recordSet": "ml:RecordSet",
            "field": "ml:Field",
            "subField": "ml:SubField",
            "dataType": "ml:dataType",
            "source": "ml:source",
            "data": "ml:data",
            "applyTransform": "ml:applyTransform",
            "format": "ml:format",
            "regex": "ml:regex",
            "separator": "ml:separator",
        },
        "@type": "sc:Dataset",
        "@language": "en",
        "name": "mydataset",
        "url": "https://www.google.com/dataset",
        "description": "This is a description.",
        "license": "This is a license.",
        "citation": "This is a citation.",
        "distribution": [
            {
                "name": "a-csv-table",
                "@type": "sc:FileObject",
                "contentUrl": "ratings.csv",
                "encodingFormat": "text/csv",
                "sha256": "xxx",
            }
        ],
        "recordSet": [
            {
                "name": "annotations",
                "@type": "ml:RecordSet",
                "field": [
                    {
                        "name": "bbox",
                        "@type": "ml:Field",
                        "description": "The bounding box around annotated object[s].",
                        "dataType": "ml:BoundingBox",
                        "source": {
                            "data": "#{a-csv-table/annotations}",
                            "format": "XYWH",
                        },
                    },
                ],
            },
        ],
    }
    expected_json_ld = [
        {
            "@type": ["https://schema.org/Dataset"],
            "http://mlcommons.org/schema/RecordSet": [{}],
            "https://schema.org/@language": [{"@value": "en"}],
            "https://schema.org/citation": [{"@value": "This is a citation."}],
            "https://schema.org/description": [{"@value": "This is a description."}],
            "https://schema.org/distribution": [{}],
            "https://schema.org/license": [{"@value": "This is a license."}],
            "https://schema.org/name": [{"@value": "mydataset"}],
            "https://schema.org/url": [{"@value": "https://www.google.com/dataset"}],
        },
        {
            "@type": ["https://schema.org/FileObject"],
            "https://schema.org/contentUrl": [{"@value": "ratings.csv"}],
            "https://schema.org/encodingFormat": [{"@value": "text/csv"}],
            "https://schema.org/name": [{"@value": "a-csv-table"}],
            "https://schema.org/sha256": [{"@value": "xxx"}],
        },
        {
            "@type": ["http://mlcommons.org/schema/RecordSet"],
            "http://mlcommons.org/schema/Field": [{}],
            "https://schema.org/name": [{"@value": "annotations"}],
        },
        {
            "@type": ["http://mlcommons.org/schema/Field"],
            "http://mlcommons.org/schema/dataType": [{"@value": "ml:BoundingBox"}],
            "http://mlcommons.org/schema/source": [{}],
            "https://schema.org/description": [
                {"@value": "The bounding box around annotated object[s]."}
            ],
            "https://schema.org/name": [{"@value": "bbox"}],
        },
        {
            "http://mlcommons.org/schema/data": [
                {"@value": "#{a-csv-table/annotations}"}
            ],
            "http://mlcommons.org/schema/format": [{"@value": "XYWH"}],
        },
    ]
    _, json_ld = from_json_to_jsonld(json)
    # We ignore `@id`, because they can change.
    assert_jsons_are_equal(expected_json_ld, json_ld, ignore_keys=["@id"])


def test_from_jsonld_to_nodes():
    issues = Issues()
    json_ld = [
        {
            "@id": "ID_DATASET",
            "@type": ["https://schema.org/Dataset"],
            "https://schema.org/@language": [{"@value": "en"}],
            "https://schema.org/citation": [{"@value": "This is a citation."}],
            "https://schema.org/description": [{"@value": "This is a description."}],
            "https://schema.org/license": [{"@value": "This is a license."}],
            "https://schema.org/name": [{"@value": "mydataset"}],
            "https://schema.org/url": [{"@value": "https://www.google.com/dataset"}],
            "https://schema.org/distribution": [{"@id": "ID_FILE_OBJECT"}],
        },
        {
            "@id": "ID_FILE_OBJECT",
            "@type": ["https://schema.org/FileObject"],
            "https://schema.org/name": [{"@value": "a-csv-table"}],
            "https://schema.org/contentUrl": [{"@value": "ratings.csv"}],
            "https://schema.org/encodingFormat": [{"@value": "text/csv"}],
            "https://schema.org/sha256": [{"@value": "xxx"}],
        },
    ]
    expected_nodes = [
        Metadata(
            issues=issues,
            name="mydataset",
            rdf_id="ID_DATASET",
            uid="mydataset",
            citation="This is a citation.",
            description="This is a description.",
            license="This is a license.",
            url="https://www.google.com/dataset",
            context=Context(
                dataset_name="mydataset",
                distribution_name=None,
                record_set_name=None,
                field_name=None,
                sub_field_name=None,
            ),
        ),
        FileObject(
            issues=issues,
            name="a-csv-table",
            rdf_id="ID_FILE_OBJECT",
            uid="a-csv-table",
            content_url="ratings.csv",
            encoding_format="text/csv",
            sha256="xxx",
            context=Context(
                dataset_name="mydataset",
                distribution_name="a-csv-table",
                record_set_name=None,
                field_name=None,
                sub_field_name=None,
            ),
        ),
    ]
    nodes, _ = from_jsonld_to_nodes(issues, json_ld)
    assert nodes == expected_nodes
