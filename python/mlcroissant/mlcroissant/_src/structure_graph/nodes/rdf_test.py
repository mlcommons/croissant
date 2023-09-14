"""Tests for RDF."""

from mlcroissant._src.structure_graph.nodes.rdf import Rdf


def test_shorten_value():
    rdf = Rdf.from_json(
        json={
            "@context": {
                "bio": "https://bioschemas.org/",
                "replace": "ml:replace",
            }
        }
    )

    # assert rdf.shorten_value("https://schema.org/name") == "sc:name"
    assert rdf.shorten_value("https://bioschemas.org/name") == "bio:name"
    # Do not replace the value if it's not a URL...
    assert rdf.shorten_value("ml:replace") == "ml:replace"
    # ...even though the value appears in the context:
    assert "ml:replace" in rdf.reverse_context()
