"""context_test module."""

import pytest

from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion


@pytest.mark.parametrize(
    ["jsondl_conforms_to", "expected_conforms_to"],
    [
        [
            ["http://mlcommons.org/croissant/1.0", "http://myorg/coolspec/0.1b"],
            CroissantVersion.V_1_0,
        ],
        [
            ["http://myorg/coolspec/0.1b", "http://mlcommons.org/croissant/1.0"],
            CroissantVersion.V_1_0,
        ],
        [
            "http://mlcommons.org/croissant/1.0",
            CroissantVersion.V_1_0,
        ],
    ],
)
def test_croissant_version_from_jsonld(jsondl_conforms_to, expected_conforms_to):
    ctx = Context()
    ctx.conforms_to = CroissantVersion.from_jsonld(ctx, jsondl_conforms_to)
    assert ctx.conforms_to == expected_conforms_to


@pytest.mark.parametrize(
    ["jsondl_conforms_to", "error_msg"],
    [
        [
            123,
            (
                "At least one of the provided conformsTo should be a valid"
                " CroissantVersion. Got: 123"
            ),
        ],
        [
            ["http://myorg/coolspec/0.1b", "http://myorg/coolspec/0.1c"],
            (
                "At least one of the provided conformsTo should be a valid"
                " CroissantVersion. Got: ['http://myorg/coolspec/0.1b',"
                " 'http://myorg/coolspec/0.1c']"
            ),
        ],
    ],
)
def test_invalid_croissant_version_from_jsonld(jsondl_conforms_to, error_msg):
    ctx = Context()
    ctx.conforms_to = CroissantVersion.from_jsonld(ctx, jsondl_conforms_to)
    assert error_msg in ctx.issues.errors
