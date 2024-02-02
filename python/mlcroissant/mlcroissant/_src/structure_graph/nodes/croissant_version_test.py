"""Tests for CroissantVersion."""

import pytest

from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion


@pytest.mark.parametrize(
    "conforms_to",
    [1, 1.0, "1.0"],
)
def test_conforms_to_is_invalid(conforms_to):
    ctx = Context(conforms_to=conforms_to)
    assert any(
        error.startswith("conformsTo should be a string or a CroissantVersion.")
        for error in ctx.issues.errors
    )


@pytest.mark.parametrize(
    ["conforms_to", "expected"],
    [
        [None, CroissantVersion.V_0_8],
        ["http://mlcommons.org/croissant/0.8", CroissantVersion.V_0_8],
        ["http://mlcommons.org/croissant/1.0", CroissantVersion.V_1_0],
        [CroissantVersion.V_0_8, CroissantVersion.V_0_8],
        [CroissantVersion.V_1_0, CroissantVersion.V_1_0],
    ],
)
def test_conforms_to_is_checked(conforms_to, expected: CroissantVersion):
    # If left empty, conforms_to defaults to 0.8.
    ctx = Context()
    assert CroissantVersion.from_jsonld(ctx, conforms_to) == expected
    assert not ctx.issues.errors
    assert not ctx.issues.warnings
