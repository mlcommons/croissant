"""base_node_test module."""

import dataclasses

from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph import base_node


def test_there_exists_at_least_one_property():
    @dataclasses.dataclass(frozen=True, repr=False)
    class Node(base_node.Node):
        property1: str = ""
        property2: str = ""

        def check(self):
            pass

    node = Node(issues=Issues(), property1="property1", property2="property2")
    assert base_node.there_exists_at_least_one_property(
        node, ["property0", "property1"]
    )
    assert not base_node.there_exists_at_least_one_property(node, [])
    assert not base_node.there_exists_at_least_one_property(node, ["property0"])


def test_repr():
    @dataclasses.dataclass(frozen=True, repr=False)
    class MyNode(base_node.Node):
        foo: str = ""
        bar: str | None = None

        def check(self):
            pass

    node = MyNode(issues=Issues(), name="NAME", foo="bar", rdf_id="RDF_IR", uid="UID")
    assert str(node) == "MyNode(uid=UID, foo=bar, name=NAME)"
