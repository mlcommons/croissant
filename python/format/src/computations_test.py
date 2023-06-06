"""computations_test module."""

from etils import epath
from format.src.computations import (
    Download,
    InitOperation,
    ReadCsv,
    ReadField,
    GroupRecordSet,
)
from format.src.errors import Issues
from format.src.nodes import Node
import pytest
import rdflib
from rdflib import namespace

node = Node(
    issues=Issues(),
    graph=None,
    node=None,
    name="node_name",
    parent_uid="parent_name",
)


@pytest.mark.parametrize(
    ["operation_cls", "kwargs", "expected_str"],
    [
        (Download, {"url": "http://mlcommons.org"}, "Download(node_name)"),
        (InitOperation, {}, "InitOperation(node_name)"),
        (
            ReadCsv,
            {"croissant_folder": epath.Path(), "url": "http://mlcommons.org"},
            "ReadCsv(node_name)",
        ),
        (
            ReadField,
            {"rdf_namespace_manager": namespace.NamespaceManager},
            "ReadField(node_name)",
        ),
        (GroupRecordSet, {}, "GroupRecordSet(node_name)"),
    ],
)
def test_str_representation(operation_cls, kwargs, expected_str):
    operation = operation_cls(node=node, **kwargs)
    assert str(operation) == expected_str


def test_find_data_type():
    sc = rdflib.Namespace("https://schema.org/")
    rdf_namespace_manager = namespace.NamespaceManager(rdflib.Graph())
    rdf_namespace_manager.bind("sc", sc)
    read_field = ReadField(node=node, rdf_namespace_manager=rdf_namespace_manager)
    assert read_field.find_data_type("sc:Boolean") == bool
    assert read_field.find_data_type(["sc:Boolean", "bar"]) == bool
    assert read_field.find_data_type(["bar", "sc:Boolean"]) == bool
    with pytest.raises(ValueError, match="Unknown data type"):
        read_field.find_data_type("sc:Foo")
