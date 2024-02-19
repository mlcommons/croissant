"""base_node_test module."""

import dataclasses

import pytest

from mlcroissant._src.structure_graph import base_node
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
    ["name", "expected_errors"],
    [
        [
            "a-regular-id",
            [],
        ],
        [
            "a" * 256,
            [
                "The identifier"
                ' "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"'
                " is too long (>255 characters)."
            ],
        ],
        [
            "this is not valid",
            ['The identifier "this is not valid" contains forbidden characters.'],
        ],
        [
            {"not": {"a": {"string"}}},
            ["The identifier should be a string. Got: <class 'dict'>."],
        ],
    ],
)
def test_validate_name(name, expected_errors):
    node = create_test_node(
        Node,
        name=name,
    )
    node.validate_name()
    for expected_error, error in zip(expected_errors, node.ctx.issues.errors):
        assert expected_error in error


def test_eq():
    node1 = create_test_node(Node, uuid="node1", name="node1")
    node2 = create_test_node(Node, uuid="node2", name="node2")
    node1_doppelganger = create_test_node(Node, uuid="node1", name="node1_doppelganger")
    # Same UUID.
    assert node1 == node1_doppelganger
    # Different UUID.
    assert node1 != node2
