"""Tests for RDF to JSON-LD conversion."""

import json
import os
from tempfile import NamedTemporaryFile

import pytest
from rdflib import Graph

from croissant_rdf._src.rdf_to_jsonld import RDFConverter


def test_convert_from_rdf():
    """Test converting an RDF file back to JSON-LD."""
    # Create a simple RDF file
    with NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as fp:
        fp.write(
            """
@prefix cr: <http://mlcommons.org/croissant/> .
@prefix schema: <https://schema.org/> .

<https://example.org/dataset1> a schema:Dataset ;
    schema:name "Test Dataset" ;
    schema:description "A test dataset" .
"""
        )
        ttl_file = fp.name

    try:
        converter = RDFConverter()
        jsonld_file = converter.convert_from_rdf(ttl_file)

        # Verify the JSON-LD file was created
        assert os.path.isfile(jsonld_file)
        assert jsonld_file.endswith(".jsonld")

        # Verify it's valid JSON
        with open(jsonld_file) as f:
            data = json.load(f)
            assert isinstance(data, list)
            assert len(data) > 0

        # Clean up
        os.remove(jsonld_file)
    finally:
        os.remove(ttl_file)


def test_roundtrip_conversion():
    """Test that JSON-LD -> RDF -> JSON-LD preserves the graph structure."""
    original_data = [
        {
            "@context": {
                "@vocab": "https://schema.org/",
                "cr": "http://mlcommons.org/croissant/",
            },
            "@type": "Dataset",
            "name": "Test Dataset",
            "description": "A test dataset for round-trip conversion",
        }
    ]

    with NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as ttl_fp:
        # Convert JSON-LD to RDF
        converter = RDFConverter(fname=ttl_fp.name)
        ttl_file = converter.convert_to_rdf(original_data)

        # Verify TTL was created
        assert os.path.isfile(ttl_file)

        # Convert RDF back to JSON-LD
        jsonld_file = converter.convert_from_rdf(ttl_file)

        # Verify JSON-LD was created
        assert os.path.isfile(jsonld_file)

        # Load both graphs and compare triple counts
        g1 = Graph()
        g1.parse(data=json.dumps(original_data[0]), format="json-ld")

        g2 = Graph()
        g2.parse(jsonld_file, format="json-ld")

        # Both graphs should have the same number of triples
        assert len(g1) == len(g2)

        # Clean up
        os.remove(ttl_file)
        os.remove(jsonld_file)
