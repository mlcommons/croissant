"""field_test module."""

from ml_croissant._src.operation_graph.operations import field
from ml_croissant._src.tests.nodes import empty_node
from rdflib import namespace


def test_str_representation():
    operation = field.ReadField(
        node=empty_node, rdf_namespace_manager=namespace.NamespaceManager
    )
    assert str(operation) == "ReadField(node_name)"
