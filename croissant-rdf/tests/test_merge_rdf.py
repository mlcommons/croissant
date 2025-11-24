"""Tests for merging RDF files."""

import os
from tempfile import NamedTemporaryFile

from rdflib import Graph

from croissant_rdf._src.merge_rdf import merge_rdf_files


def test_merge_two_rdf_files():
    """Test merging two RDF files."""
    # Create two RDF files with different datasets
    with NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as fp1:
        fp1.write(
            """
@prefix schema: <https://schema.org/> .

<https://example.org/dataset1> a schema:Dataset ;
    schema:name "Dataset 1" ;
    schema:description "First dataset" .
"""
        )
        file1 = fp1.name

    with NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as fp2:
        fp2.write(
            """
@prefix schema: <https://schema.org/> .

<https://example.org/dataset2> a schema:Dataset ;
    schema:name "Dataset 2" ;
    schema:description "Second dataset" .
"""
        )
        file2 = fp2.name

    with NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as fp_out:
        output_file = fp_out.name

    try:
        # Merge the files
        result = merge_rdf_files([file1, file2], output_file)

        # Verify output file was created
        assert os.path.isfile(result)

        # Load and verify the merged graph
        g = Graph()
        g.parse(result)

        # Should have triples from both files (2 datasets × 3 triples each = 6 triples)
        assert len(g) == 6

        # Verify both datasets are present
        query = """
        SELECT (COUNT(?s) as ?count)
        WHERE {
            ?s a <https://schema.org/Dataset> .
        }
        """
        result_set = list(g.query(query))
        dataset_count = int(result_set[0][0])
        assert dataset_count == 2

    finally:
        # Clean up
        for f in [file1, file2, output_file]:
            if os.path.exists(f):
                os.remove(f)


def test_merge_deduplicates_triples():
    """Test that merging deduplicates overlapping triples."""
    # Create two files with overlapping content
    shared_triple = """
@prefix schema: <https://schema.org/> .

<https://example.org/shared> a schema:Dataset ;
    schema:name "Shared Dataset" .
"""

    with NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as fp1:
        fp1.write(shared_triple)
        file1 = fp1.name

    with NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as fp2:
        fp2.write(shared_triple)
        file2 = fp2.name

    with NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as fp_out:
        output_file = fp_out.name

    try:
        # Merge the files
        merge_rdf_files([file1, file2], output_file, deduplicate=True)

        # Load merged graph
        g = Graph()
        g.parse(output_file)

        # Should have only 2 triples (deduplicated), not 4
        assert len(g) == 2

    finally:
        # Clean up
        for f in [file1, file2, output_file]:
            if os.path.exists(f):
                os.remove(f)


def test_merge_different_formats():
    """Test merging files in different RDF formats."""
    # Create Turtle file
    with NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as fp_ttl:
        fp_ttl.write(
            """
@prefix schema: <https://schema.org/> .
<https://example.org/dataset1> a schema:Dataset .
"""
        )
        ttl_file = fp_ttl.name

    # Create N-Triples file
    with NamedTemporaryFile(mode="w", suffix=".nt", delete=False) as fp_nt:
        fp_nt.write(
            "<https://example.org/dataset2> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <https://schema.org/Dataset> .\n"
        )
        nt_file = fp_nt.name

    with NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as fp_out:
        output_file = fp_out.name

    try:
        # Merge files with different formats
        merge_rdf_files([ttl_file, nt_file], output_file)

        # Verify merged graph
        g = Graph()
        g.parse(output_file)

        # Should have 2 triples from both files
        assert len(g) == 2

    finally:
        # Clean up
        for f in [ttl_file, nt_file, output_file]:
            if os.path.exists(f):
                os.remove(f)


def test_merge_to_jsonld_format():
    """Test merging and outputting as JSON-LD."""
    with NamedTemporaryFile(mode="w", suffix=".ttl", delete=False) as fp:
        fp.write(
            """
@prefix schema: <https://schema.org/> .
<https://example.org/dataset1> a schema:Dataset ;
    schema:name "Test" .
"""
        )
        input_file = fp.name

    with NamedTemporaryFile(mode="w", suffix=".jsonld", delete=False) as fp_out:
        output_file = fp_out.name

    try:
        # Merge to JSON-LD format
        result = merge_rdf_files([input_file], output_file, output_format="json-ld")

        # Verify file exists and is valid JSON-LD
        assert os.path.isfile(result)

        import json

        with open(result) as f:
            data = json.load(f)
            assert isinstance(data, list)

    finally:
        # Clean up
        for f in [input_file, output_file]:
            if os.path.exists(f):
                os.remove(f)
