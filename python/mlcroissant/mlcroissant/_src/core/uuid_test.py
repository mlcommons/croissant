"""uuid_test module."""

from unittest import mock

import pytest

from mlcroissant._src.core.constants import BASE_IRI
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
import mlcroissant._src.core.uuid as uuid_lib


@pytest.mark.parametrize(
    ["input_uuid", "output", "base_iri"],
    [
        [f"aaa{BASE_IRI}bbb", "bbb", BASE_IRI],
        [f"aaa{BASE_IRI}b{BASE_IRI}bb", f"b{BASE_IRI}bb", BASE_IRI],
        [{"@id": f"aaa{BASE_IRI}bbb"}, "bbb", BASE_IRI],
        [{"@id": "aaa"}, "aaa", BASE_IRI],
        ["aaa", "aaa", BASE_IRI],
        [f"{BASE_IRI}aaa", "aaa", BASE_IRI],
        ["aaa/CUSTOM_IRI/bbb", "bbb", "/CUSTOM_IRI/"],
        [{"@id": "aaa/CUSTOM_IRI/b/CUSTOM_IRI/bb"}, "b/CUSTOM_IRI/bb", "/CUSTOM_IRI/"],
    ],
)
def test_uuid_from_jsonld(input_uuid, output, base_iri):
    ctx = Context(base_iri=base_iri)
    uuid = uuid_lib.Uuid.from_jsonld(ctx=ctx, jsonld=input_uuid)
    assert uuid.uuid == output


@pytest.mark.parametrize(
    ["input_uuid", "output", "base_iri"],
    [
        [None, "123456", BASE_IRI],
        [None, "123456", "/CUSTOM_IRI/"],
        [{"@id": None}, "123456", BASE_IRI],
        [{"@id": None}, "123456", "/CUSTOM_IRI/"],
    ],
)
@mock.patch.object(uuid_lib, "generate_uuid")
def test_uuid_from_none_jsonld(
    mock_uuid_lib_generate_uuid, input_uuid, output, base_iri
):
    mock_uuid_lib_generate_uuid.return_value = "123456"
    ctx = Context()
    ctx.rdf.context["@base"] = base_iri
    uuid = uuid_lib.Uuid.from_jsonld(ctx=ctx, jsonld=input_uuid)
    assert uuid.uuid == output


@pytest.mark.parametrize(
    ["input_uuid", "output"], [[f"aaa{BASE_IRI}bbb", "bbb"], ["aaa", "aaa"]]
)
def test_uuid_to_jsonld(input_uuid, output):
    ctx = Context()
    ctx.rdf.context["@base"] = BASE_IRI
    uuid = uuid_lib.Uuid(ctx=ctx, uuid=input_uuid)
    assert uuid.to_jsonld() == output


@pytest.mark.parametrize(
    ["conforms_to", "uuid", "output"],
    [
        [CroissantVersion.V_0_8, "example/uuid", "example/uuid"],
        [CroissantVersion.V_1_0, "example/uuid", {"@id": "example/uuid"}],
    ],
)
def test_formatted_uuid_to_json(conforms_to, uuid, output):
    ctx = Context(conforms_to=conforms_to)
    ctx.rdf.context["@base"] = BASE_IRI
    uuid = uuid_lib.Uuid(ctx=ctx, uuid=uuid)
    assert uuid.formatted_uuid_to_json() == output
