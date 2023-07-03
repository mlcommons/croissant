"""graph_test module."""

from ml_croissant._src.operation_graph.operations import ReadField
from ml_croissant._src.tests.nodes import empty_node
import pytest
import rdflib
from rdflib import namespace


def test_find_data_type():
    sc = rdflib.Namespace("https://schema.org/")
    rdf_namespace_manager = namespace.NamespaceManager(rdflib.Graph())
    rdf_namespace_manager.bind("sc", sc)
    read_field = ReadField(node=empty_node, rdf_namespace_manager=rdf_namespace_manager)
    assert read_field.find_data_type("sc:Boolean") == bool
    assert read_field.find_data_type(["sc:Boolean", "bar"]) == bool
    assert read_field.find_data_type(["bar", "sc:Boolean"]) == bool
    with pytest.raises(ValueError, match="Unknown data type"):
        read_field.find_data_type("sc:Foo")
