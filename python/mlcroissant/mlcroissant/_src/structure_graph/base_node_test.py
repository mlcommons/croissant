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
            set(),
        ],
        [
            "a" * 256,
            {
                "The identifier"
                ' "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"'
                " is too long (>255 characters)."
            },
        ],
        [
            "this is not valid",
            {'The identifier "this is not valid" contains forbidden characters.'},
        ],
        [
            {"not": {"a": {"string"}}},
            {"The identifier should be a string. Got: <class 'dict'>."},
        ],
    ],
)
def test_validate_name(name, expected_errors):
    node = create_test_node(
        Node,
        name=name,
    )
    node.validate_name()
    assert node.issues.errors == expected_errors


def test_eq():
    node_1_with_parent_a = create_test_node(Node, name="node1")
    node_1_with_parent_a.parents = ["parentA"]
    node_1_with_parent_b = create_test_node(Node, name="node1")
    node_1_with_parent_b.parents = ["parentB"]
    node_2_with_parent_a = create_test_node(Node, name="node2")
    node_2_with_parent_a.parents = ["parentA"]
    node_2_with_parent_b = create_test_node(Node, name="node2")
    node_2_with_parent_b.parents = ["parentB"]
    assert node_1_with_parent_a == node_1_with_parent_b
    assert node_2_with_parent_a == node_2_with_parent_b
    assert node_1_with_parent_a != node_2_with_parent_a
    assert node_1_with_parent_a != node_2_with_parent_b
