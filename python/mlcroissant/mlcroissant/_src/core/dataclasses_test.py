"""dataclasses_test module."""

import pytest
from rdflib.namespace import SDO

from mlcroissant._src.core import dataclasses as mlc_dataclasses
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.structure_graph.base_node import Node


def test_dataclass():
    url = lambda ctx: "http://foo.org" if ctx.is_v0() else "http://bar.org"

    @mlc_dataclasses.dataclass
    class SomeNode:
        field1: int = mlc_dataclasses.jsonld_field(
            description="The first field",
            input_types=[SDO.Integer],
        )
        field2: list[str] = mlc_dataclasses.jsonld_field(
            cardinality="MANY",
            description="The second field",
            input_types=[SDO.Text],
            url=url,
        )

    node = SomeNode(field1=42, field2=["foo"])
    for cls_or_instance in [node, SomeNode]:
        field1, field2 = list(mlc_dataclasses.jsonld_fields(cls_or_instance))

        # Field #1
        assert field1.name == "field1"
        assert field1.cardinality == "ONE"
        assert field1.description == "The first field"
        assert field1.from_jsonld == None
        assert field1.input_types == [SDO.Integer]
        assert field1.to_jsonld == None
        assert field1.url == None

        # Field #2
        assert field2.name == "field2"
        assert field2.cardinality == "MANY"
        assert field2.description == "The second field"
        assert field2.from_jsonld == None
        assert field2.input_types == [SDO.Text]
        assert field2.to_jsonld == None
        assert field2.url == url
        assert (
            field2.call_url(Context(conforms_to=CroissantVersion.V_0_8))
            == "http://foo.org"
        )
        assert (
            field2.call_url(Context(conforms_to=CroissantVersion.V_1_0))
            == "http://bar.org"
        )


def test_jsonld_fields():
    @mlc_dataclasses.dataclass
    class SomeNode(Node):
        field1: int = mlc_dataclasses.jsonld_field(
            default=0,
            description="The first field",
            input_types=[SDO.Integer],
            versions=[CroissantVersion.V_0_8],
        )
        field2: str = mlc_dataclasses.jsonld_field(
            default="",
            description="The second field",
            input_types=[SDO.Text],
        )

    node = SomeNode(ctx=Context(conforms_to=CroissantVersion.V_1_0))
    fields = list(mlc_dataclasses.jsonld_fields(node))
    assert len(fields) == 1
    assert fields[0].name == "field2"


@pytest.mark.parametrize(
    "accessor",
    [
        # Access class
        lambda cls: cls,
        # Access instance of class
        lambda cls: cls(),
    ],
)
def test_types_of_fields(accessor):
    @mlc_dataclasses.dataclass
    class SubNode(Node):
        field: int | None = mlc_dataclasses.jsonld_field(
            default=None,
            input_types=[SDO.Text],  # this is incompatible with `int`
        )

    with pytest.raises(TypeError, match='Field "SubNode.field" should have type'):
        list(mlc_dataclasses.jsonld_fields(accessor(SubNode)))

    @mlc_dataclasses.dataclass
    class SubNode(Node):
        field: int = mlc_dataclasses.jsonld_field(
            default=None,  # this is incompatible with `int` (expect int | None)
            input_types=[SDO.Integer],
        )

    with pytest.raises(TypeError, match='Field "SubNode.field" should have type'):
        list(mlc_dataclasses.jsonld_fields(accessor(SubNode)))

    @mlc_dataclasses.dataclass
    class SubNode(Node):
        field: str = mlc_dataclasses.jsonld_field(
            default_factory=Node,  # this is incompatible with str
            input_types=[Node],
        )

    with pytest.raises(TypeError, match='Field "SubNode.field" should have type'):
        list(mlc_dataclasses.jsonld_fields(accessor(SubNode)))

    def cast_fn(value: Node) -> int:  # int is incompatible with Node
        del value
        return 0

    @mlc_dataclasses.dataclass
    class SubNode(Node):
        field: Node = mlc_dataclasses.jsonld_field(
            cast_fn=cast_fn,
            default_factory=Node,
            input_types=[Node],
        )

    with pytest.raises(TypeError, match='Field "SubNode.field" .* should have type'):
        list(mlc_dataclasses.jsonld_fields(accessor(SubNode)))
