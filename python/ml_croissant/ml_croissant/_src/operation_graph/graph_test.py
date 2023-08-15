"""graph_test module."""

import pytest
from rdflib import term

from ml_croissant._src.operation_graph.operations import ReadField
from ml_croissant._src.tests.nodes import empty_field


def test_find_data_type():
    read_field = ReadField(node=empty_field)
    assert read_field.find_data_type(term.URIRef("https://schema.org/Boolean")) == bool
    assert (
        read_field.find_data_type([term.URIRef("https://schema.org/Boolean"), "bar"])
        == bool
    )
    assert (
        read_field.find_data_type(["bar", term.URIRef("https://schema.org/Boolean")])
        == bool
    )
    with pytest.raises(ValueError, match="Unknown data type"):
        read_field.find_data_type("sc:Foo")
