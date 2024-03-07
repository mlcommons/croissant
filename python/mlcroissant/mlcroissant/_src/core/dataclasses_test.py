"""dataclasses_test module."""

from rdflib.namespace import SDO

from mlcroissant._src.core import dataclasses as mlc_dataclasses
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion


def test_dataclass():
    url = lambda ctx: "http://foo.org" if ctx.is_v0() else "http://bar.org"

    @mlc_dataclasses.dataclass
    class SomeNode:
        field1: int = mlc_dataclasses.jsonld_field(description="The first field")
        field2: str = mlc_dataclasses.jsonld_field(
            cardinality="MANY",
            description="The second field",
            input_types=[SDO.Text],
            required=True,
            url=url,
        )

    node = SomeNode(field1=42, field2="foo")
    for cls_or_instance in [node, SomeNode]:
        field1, field2 = list(mlc_dataclasses.jsonld_fields(cls_or_instance))

        # Field #1
        assert field1.name == "field1"
        assert field1.cardinality == "ONE"
        assert field1.description == "The first field"
        assert field1.from_jsonld == None
        assert field1.input_types == []
        assert field1.to_jsonld == None
        assert field1.required == False
        assert field1.url == None

        # Field #2
        assert field2.name == "field2"
        assert field2.cardinality == "MANY"
        assert field2.description == "The second field"
        assert field2.from_jsonld == None
        assert field2.input_types == [SDO.Text]
        assert field2.to_jsonld == None
        assert field2.required == True
        assert field2.url == url
        assert (
            field2.call_url(Context(conforms_to=CroissantVersion.V_0_8))
            == "http://foo.org"
        )
        assert (
            field2.call_url(Context(conforms_to=CroissantVersion.V_1_0))
            == "http://bar.org"
        )
