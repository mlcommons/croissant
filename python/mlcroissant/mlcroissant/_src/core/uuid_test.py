"""uuid_test module."""

from unittest import mock

import pytest

from mlcroissant._src.core.constants import BASE_IRI
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
import mlcroissant._src.core.uuid as uuid_lib


@pytest.mark.parametrize(
    ["input", "output"],
    [
        [f"aaa{BASE_IRI}bbb", "bbb"],
        [f"aaa{BASE_IRI}b{BASE_IRI}bb", f"b{BASE_IRI}bb"],
        [{"@id": "aaa"}, "aaa"],
        ["aaa", "aaa"],
        [f"{BASE_IRI}aaa", "aaa"],
        [f"aaa{BASE_IRI}", ""],
    ],
)
def test_uuid_from_jsonld(input, output):
    assert uuid_lib.uuid_from_jsonld(input) == output


@mock.patch.object(uuid_lib, "generate_uuid")
def test_uuid_from_jsonld_generate_uuid(mock_uuid_lib_generate_uuid):
    mock_uuid_lib_generate_uuid.return_value = "123456"
    assert uuid_lib.uuid_from_jsonld(None) == "123456"


@pytest.mark.parametrize(
    ["input", "output"], [[f"aaa{BASE_IRI}bbb", "bbb"], ["aaa", "aaa"]]
)
def test_uuid_to_jsonld(input, output):
    assert uuid_lib.uuid_to_jsonld(input) == output


@pytest.mark.parametrize(
    ["conforms_to", "uuid", "output"],
    [
        [CroissantVersion.V_0_8, "example/uuid", "example/uuid"],
        [CroissantVersion.V_1_0, "example/uuid", {"@id": "example/uuid"}],
        [
            CroissantVersion.V_1_0,
            ["example/uuid1", "example/uuid2"],
            [{"@id": "example/uuid1"}, {"@id": "example/uuid2"}],
        ],
        [CroissantVersion.V_1_0, ["example/uuid1"], {"@id": "example/uuid1"}],
    ],
)
def test_formatted_uuid_to_json(conforms_to, uuid, output):
    ctx = Context(conforms_to=conforms_to)
    assert uuid_lib.formatted_uuid_to_json(ctx=ctx, uuid=uuid) == output
