"""base_node_test module."""

import dataclasses
import json

from etils import epath
from ml_croissant._src.structure_graph import base_node


def test_there_exists_at_least_one_property():
    @dataclasses.dataclass
    class Node:
        property1: str
        property2: str

    node = Node(property1="property1", property2="property2")
    # pylint:disable=protected-access
    assert base_node.there_exists_at_least_one_property(node, ["property0", "property1"])
    assert not base_node.there_exists_at_least_one_property(node, [])
    assert not base_node.there_exists_at_least_one_property(node, ["property0"])
