"""Tests for RDF."""

from unittest import mock

from absl import logging
import pytest

from mlcroissant._src.core.context import Context
from mlcroissant._src.core.rdf import make_context
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
    assert rdf.shorten_value("https://bioschemas.org/name") == "bio:name"
    # Do not replace the value if it's not a URL...
    assert rdf.shorten_value("ml:replace") == "ml:replace"
    # ...even though the value appears in the context:
    assert "ml:replace" in rdf.reverse_context()


@pytest.mark.parametrize(
    "ctx",
    [None] + [Context(conforms_to=conforms_to) for conforms_to in CONFORMS_TO],
)
def test_shorten_key(ctx):
    rdf = Rdf.from_json(
        ctx=ctx,
        json={
            "@context": {
                "@vocab": "https://base.org/",
                "bio": "https://bioschemas.org/",
                "bar": "bio:bar",
                "baz": {"@id": "bio:baz"},
                "replace": "ml:replace",
            }
        },
    )
    assert rdf.shorten_key("https://base.org/foo") == "foo"
    assert rdf.shorten_key("https://bioschemas.org/name") == "bio:name"
    assert rdf.shorten_key("bio:name") == "bio:name"
    assert rdf.shorten_key("https://bioschemas.org/bar") == "bar"
    assert rdf.shorten_key("bio:bar") == "bar"
    assert rdf.shorten_key("https://bioschemas.org/baz") == "baz"
    assert rdf.shorten_key("bio:baz") == "baz"


@mock.patch.object(logging, "warning")
def test_from_json_without_warning(mock_warning):
    jsonld = {"@context": make_context()}
    rdf = Rdf.from_json(Context(), jsonld)
    assert rdf.context == make_context()
    mock_warning.assert_not_called()


@mock.patch.object(logging, "warning")
def test_from_json_with_warning(mock_warning):
    jsonld = {"@context": {"foo": "bar"}}
    rdf = Rdf.from_json(Context(), jsonld)
    assert rdf.context == {"foo": "bar"}
    mock_warning.assert_called_once()
