"""Tests for RDF."""

import pytest

from mlcroissant._src.core.context import Context
from mlcroissant._src.core.rdf import Rdf
from mlcroissant._src.tests.versions import CONFORMS_TO


@pytest.mark.parametrize(
    "ctx",
    [None] + [Context(conforms_to=conforms_to) for conforms_to in CONFORMS_TO],
)
def test_shorten_value(ctx):
    rdf = Rdf.from_json(
        ctx=ctx,
        json={
            "@context": {
                "bio": "https://bioschemas.org/",
                "replace": "ml:replace",
            }
        },
    )

    # assert rdf.shorten_value("https://schema.org/name") == "sc:name"
    assert rdf.shorten_value("https://bioschemas.org/name") == "bio:name"
    # Do not replace the value if it's not a URL...
    assert rdf.shorten_value("ml:replace") == "ml:replace"
    # ...even though the value appears in the context:
    assert "ml:replace" in rdf.reverse_context()
