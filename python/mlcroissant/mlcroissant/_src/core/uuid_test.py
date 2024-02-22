"""uuid_test module."""

from unittest import mock

import pytest

from mlcroissant._src.core.constants import BASE_IRI
import mlcroissant._src.core.uuid as uuid_lib


@pytest.mark.parametrize(
    ["input", "output"],
    [[f"aaa{BASE_IRI}bbb", f"aaa{BASE_IRI}bbb"], [{"@id": "aaa"}, "aaa"]],
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
