"""field_test module."""

from ml_croissant._src.operation_graph.operations import field
from ml_croissant._src.tests.nodes import empty_field
from rdflib import namespace


def test_str_representation():
    operation = field.ReadField(
        node=empty_field, rdf_namespace_manager=namespace.NamespaceManager
    )
    assert str(operation) == "ReadField(field_name)"
