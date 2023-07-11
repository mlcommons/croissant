"""base_node_test module."""

import dataclasses

from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph import base_node
import networkx as nx
from rdflib import term


def test_there_exists_at_least_one_property():
    @dataclasses.dataclass(frozen=True, repr=False)
    class Node(base_node.Node):
        property1: str = ""
        property2: str = ""

        def check(self):
            pass

    node = Node(
        issues=Issues(),
        bnode=term.BNode("rdf_id"),
        graph=nx.MultiDiGraph(),
        parents=(),
        name="name",
        property1="property1",
        property2="property2",
    )
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

    node = MyNode(
        issues=Issues(),
        bnode=term.BNode("rdf_id"),
        graph=nx.MultiDiGraph(),
        parents=(),
        name="name",
        foo="foo",
    )
    assert str(node) == "MyNode(uid=name, foo=foo, name=name)"
