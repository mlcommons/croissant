"""uuid_test module."""

import pytest

from mlcroissant._src.core.constants import BASE_IRI
from mlcroissant._src.core.uuid import uuid_to_jsonld


@pytest.mark.parametrize(
    ["input", "output"], [[f"aaa{BASE_IRI}bbb", "bbb"], ["aaa", "aaa"]]
)
def test_uuid_to_jsonld(input, output):
    assert uuid_to_jsonld(input) == output
