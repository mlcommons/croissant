"""base_node_test module."""

import dataclasses

import pytest
from rdflib.namespace import SDO

from mlcroissant._src.core import dataclasses as mlc_dataclasses
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.structure_graph import base_node
from mlcroissant._src.tests.nodes import assert_contain_error
from mlcroissant._src.tests.nodes import assert_contain_warning
from mlcroissant._src.tests.nodes import create_test_node


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
