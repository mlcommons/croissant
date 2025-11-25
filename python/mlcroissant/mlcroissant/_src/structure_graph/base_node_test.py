"""base_node_test module."""

import dataclasses
from unittest import mock

import pytest
from rdflib.namespace import SDO

from mlcroissant._src.core import dataclasses as mlc_dataclasses
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.structure_graph import base_node
from mlcroissant._src.core.json_ld import expand_jsonld
from mlcroissant._src.core.rdf import Rdf
from mlcroissant._src.structure_graph.nodes.metadata import Metadata
from mlcroissant._src.tests.nodes import assert_contain_error
from mlcroissant._src.tests.nodes import assert_contain_warning
from mlcroissant._src.tests.nodes import create_test_node
import os
from rdflib import term
from mlcroissant._src.core import constants


@dataclasses.dataclass(eq=False, repr=False)
class Node(base_node.Node):
    property1: str = ""
    property2: str = ""

    @classmethod
    def from_jsonld(cls):
        pass

    def to_json(self):
        pass


def test_there_exists_at_least_one_property():
    node = create_test_node(
        Node,
        property1="property1",
        property2="property2",
    )
    assert node.there_exists_at_least_one_property(["property0", "property1"])
    assert not node.there_exists_at_least_one_property([])
    assert not node.there_exists_at_least_one_property(["property0"])


@pytest.mark.parametrize(
    ["name", "expected_errors", "conforms_to"],
    [
        [
            "a" * 256,
            [
                "The name"
                ' "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"'
                " is too long (>255 characters)."
            ],
            CroissantVersion.V_0_8,
        ],
        [
            "this is not valid",
            ['The name "this is not valid" contains forbidden characters.'],
            CroissantVersion.V_0_8,
        ],
        [
            {"not": {"a": {"string"}}},
            ["The name should be a string. Got: <class 'dict'>."],
            CroissantVersion.V_1_0,
        ],
        [
            False,
            ["The name should be a string or dict. Got: <class 'bool'>."],
            CroissantVersion.V_1_1,
        ],
    ],
)
def test_validate_name(name, expected_errors, conforms_to):
    node = create_test_node(Node, name=name, ctx=Context(conforms_to=conforms_to))
    node.validate_name()
    assert node.ctx.issues.errors
    for expected_error, error in zip(expected_errors, node.ctx.issues.errors):
        assert expected_error in error


@pytest.mark.parametrize(
    "conforms_to", [CroissantVersion.V_0_8, CroissantVersion.V_1_0]
)
def test_validate_correct_name(conforms_to):
    node = create_test_node(
        Node, name="a-regular-id", ctx=Context(conforms_to=conforms_to)
    )
    node.validate_name()
    assert not node.ctx.issues.errors


def test_validate_name_1_0():
    node = create_test_node(
        Node, name="this is not valid", ctx=Context(conforms_to=CroissantVersion.V_1_0)
    )
    node.validate_name()
    assert not node.ctx.issues.errors


def test_eq():
    node1 = create_test_node(Node, id="node1", name="node1")
    node2 = create_test_node(Node, id="node2", name="node2")
    node1_doppelganger = create_test_node(Node, id="node1", name="node1_doppelganger")
    # Same ID.
    assert node1 == node1_doppelganger
    # Different ID.
    assert node1 != node2


def test_custom_node_with_cardinality_one():
    @mlc_dataclasses.dataclass
    class CustomNode(base_node.Node):
        JSONLD_TYPE = "foo.org/CustomNode"

        property1: int | None = mlc_dataclasses.jsonld_field(
            cardinality="ONE",
            default=None,
            input_types=[SDO.Integer],
            url="foo.org/property1",
        )

    node = CustomNode.from_jsonld(
        Context(),
        {
            "@type": "foo.org/CustomNode",
            "@id": "foo",
            "foo.org/property1": 42,
        },
    )
    assert node.property1 == 42
    assert not node.ctx.issues.errors
    assert node.to_json() == {
        "@id": "foo",
        "@type": "foo.org/CustomNode",
        "foo.org/property1": 42,
    }

    node = CustomNode.from_jsonld(
        Context(),
        {
            "@type": "foo.org/CustomNode",
            "@id": "foo",
            "foo.org/property1": [42, 43],
        },
    )
    assert node.property1 == 42
    assert_contain_warning(
        node.ctx.issues, "`property1` has cardinality `ONE`, but got a list"
    )


def test_custom_node_with_cardinality_many():
    @mlc_dataclasses.dataclass
    class CustomNode(base_node.Node):
        JSONLD_TYPE = "foo.org/CustomNode"

        property1: list[int] = mlc_dataclasses.jsonld_field(
            cardinality="MANY",
            default_factory=list,
            input_types=[SDO.Integer],
            url="foo.org/property1",
        )

    node = CustomNode.from_jsonld(
        Context(),
        {
            "@type": "foo.org/CustomNode",
            "@id": "foo",
            "foo.org/property1": [42, 43],
        },
    )
    assert node.property1 == [42, 43]
    assert not node.ctx.issues.errors
    assert node.to_json() == {
        "@id": "foo",
        "@type": "foo.org/CustomNode",
        "foo.org/property1": [42, 43],
    }

    node = CustomNode.from_jsonld(
        Context(),
        {
            "@type": "foo.org/CustomNode",
            "@id": "foo",
            "foo.org/property1": 42,
        },
    )
    assert node.property1 == [42]
    assert node.to_json() == {
        "@id": "foo",
        "@type": "foo.org/CustomNode",
        "foo.org/property1": 42,
    }


def test_custom_node_with_input_types():
    @mlc_dataclasses.dataclass
    class ChildNode(base_node.Node):
        JSONLD_TYPE = "foo.org/ChildNode"

        child: str | None = mlc_dataclasses.jsonld_field(
            default=None,
            input_types=[SDO.Text],
            url="foo.org/child",
        )

    @mlc_dataclasses.dataclass
    class CustomNode(base_node.Node):
        JSONLD_TYPE = "foo.org/CustomNode"

        property1: int | None = mlc_dataclasses.jsonld_field(
            default=None,
            input_types=[SDO.Integer],
            url="foo.org/property1",
        )
        # pytype: disable=invalid-annotation, disable=name-error
        property2: list[ChildNode] = mlc_dataclasses.jsonld_field(
            cardinality="MANY",
            default_factory=list,
            input_types=[ChildNode],
            url="foo.org/property2",
        )
        # pytype: enable=invalid-annotation, enable=name-error

    # When from_jsonld succeeds:
    node = CustomNode.from_jsonld(
        Context(),
        {
            "@type": "foo.org/CustomNode",
            "@id": "foo",
            "foo.org/property1": 42,
            "foo.org/property2": [
                {
                    "@type": "foo.org/ChildNode",
                    "@id": "child",
                    "foo.org/child": "this is the child",
                }
            ],
        },
    )
    assert node.property1 == 42
    assert len(node.property2) == 1
    assert node.property2[0].id == "child"
    assert node.property2[0].child == "this is the child"
    assert not node.ctx.issues.errors
    assert not node.ctx.issues.warnings
    assert node.to_json() == {
        "@type": "foo.org/CustomNode",
        "@id": "foo",
        "foo.org/property1": 42,
        "foo.org/property2": {
            "@type": "foo.org/ChildNode",
            "@id": "child",
            "foo.org/child": "this is the child",
        },
    }

    # When from_jsonld fails:
    node = CustomNode.from_jsonld(
        Context(),
        {
            "@type": "foo.org/CustomNode",
            "@id": "foo",
            "foo.org/property1": "this should be int",
            "foo.org/property2": ["this should be child node"],
        },
    )
    assert node.property1 == None
    assert node.property2 == []
    assert_contain_error(
        node.ctx.issues,
        "`property1` should have type https://schema.org/Integer, but got str",
    )
    assert_contain_error(
        node.ctx.issues, "`property2` should have type foo.org/ChildNode, but got str"
    )


def test_cast_fn():
    def node(cast_fn):
        @mlc_dataclasses.dataclass
        class Node(base_node.Node):
            JSONLD_TYPE = None

            field: int | None = mlc_dataclasses.jsonld_field(
                default=None,
                cast_fn=cast_fn,
                input_types=[SDO.Text],
                url="foo.org/property1",
            )

        return Node

    def cast_fn(value) -> int | None:
        del value
        return 42

    Node = node(cast_fn)
    assert Node(field="field").field == 42

    def cast_fn(value) -> int | None:
        del value
        raise ValueError("bad value")

    Node = node(cast_fn)
    assert Node(field="field").field == "field"
    assert_contain_error(Node(field="field").issues, "bad value")


def test_external_vocabularies():
    jsonld = {
        "@context": {
            "@language": "en",
            "@vocab": "https://schema.org/",
            "citeAs": "cr:citeAs",
            "column": "cr:column",
            "conformsTo": "dct:conformsTo",
            "cr": "http://mlcommons.org/croissant/",
            "rai": "http://mlcommons.org/croissant/RAI/",
            "data": {"@id": "cr:data", "@type": "@json"},
            "dataType": {"@id": "cr:dataType", "@type": "@vocab"},
            "dct": "http://purl.org/dc/terms/",
            "examples": {"@id": "cr:examples", "@type": "@json"},
            "extract": "cr:extract",
            "field": "cr:field",
            "fileProperty": "cr:fileProperty",
            "fileObject": "cr:fileObject",
            "fileSet": "cr:fileSet",
            "format": "cr:format",
            "includes": "cr:includes",
            "isLiveDataset": "cr:isLiveDataset",
            "jsonPath": "cr:jsonPath",
            "key": "cr:key",
            "md5": "cr:md5",
            "parentField": "cr:parentField",
            "path": "cr:path",
            "recordSet": "cr:recordSet",
            "references": "cr:references",
            "regex": "cr:regex",
            "repeated": "cr:repeated",
            "replace": "cr:replace",
            "samplingRate": "cr:samplingRate",
            "sc": "https://schema.org/",
            "separator": "cr:separator",
            "source": "cr:source",
            "subField": "cr:subField",
            "transform": "cr:transform",
            "prov": "http://www.w3.org/ns/prov#",
        },
        "@type": "sc:Dataset",
        "name": "test-dataset",
        "conformsTo": "http://mlcommons.org/croissant/1.0",
        "prov:wasDerivedFrom": "http://example.com/source-dataset",
        "recordSet": [
            {
                "@type": "cr:RecordSet",
                "name": "test-record-set",
                "field": [
                    {
                        "@type": "cr:Field",
                        "name": "test-field",
                        "cr:equivalentProperty": "http://schema.org/name",
                        "dataType": "sc:Text",
                        "source": {"fileObject": {"@id": "test-file"}},
                    }
                ],
            }
        ],
        "distribution": [
            {
                "@id": "test-file",
                "@type": "cr:FileObject",
                "name": "test-file",
                "contentUrl": "http://example.com/data.csv",
                "encodingFormat": "text/csv",
                "sha256": "...",
            }
        ],
    }
    ctx = Context()
    ctx.rdf = Rdf.from_json(ctx, jsonld)
    expanded_jsonld = expand_jsonld(jsonld, ctx)
    metadata = Metadata.from_jsonld(ctx, expanded_jsonld)
    assert not ctx.issues.errors
    assert metadata.extra_properties == {
        "prov:wasDerivedFrom": "http://example.com/source-dataset"
    }
    assert metadata.record_sets[0].fields[0].equivalentProperty == [
        "http://schema.org/name"
    ]

    # Test serialization
    serialized = metadata.to_json()
    assert serialized["prov:wasDerivedFrom"] == "http://example.com/source-dataset"
    assert (
        serialized["recordSet"][0]["field"][0]["cr:equivalentProperty"]
        == "http://schema.org/name"
    )


@pytest.mark.parametrize(
    "value, expected_output",
    [
        # 1. Standard URI shortening
        ("http://www.w3.org/ns/prov#wasGeneratedBy", "prov:wasGeneratedBy"),
        # 2. URIRef shortening
        (term.URIRef("http://www.w3.org/ns/prov#wasGeneratedBy"), "prov:wasGeneratedBy"),
        # 3. Local base IRI stripping
        (
            f"file:///mock/cwd/{constants.BASE_IRI}some-id",
            "some-id",
        ),
        # 4. Dictionary key and value shortening
        (
            {
                "http://www.w3.org/ns/prov#atLocation": "https://example.com",
                "@id": "_:b0",
            },
            {"prov:atLocation": "https://example.com"},
        ),
        # 5. List shortening
        (
            ["http://www.w3.org/ns/prov#wasGeneratedBy", "other-value"],
            ["prov:wasGeneratedBy", "other-value"],
        ),
        # 6. Other types
        (123, 123),
        (True, True),
        (None, None),
    ],
)
def test_compact_jsonld_value(value, expected_output):
    with mock.patch("os.getcwd", return_value="/mock/cwd"):
        ctx = Context()
        ctx.rdf = Rdf.from_json(
            ctx,
            {
                "@context": {
                    "prov": "http://www.w3.org/ns/prov#",
                }
            },
        )
        assert base_node._compact_jsonld_value(ctx, value) == expected_output
