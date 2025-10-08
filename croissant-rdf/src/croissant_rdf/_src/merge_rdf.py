"""Merge RDF files from multiple providers into a single knowledge graph."""

import argparse
import time
from pathlib import Path
from typing import List, Optional

from rdflib import Graph

from croissant_rdf._src.utils import logger


def merge_rdf_files(
    input_files: List[str],
    output_file: str,
    output_format: str = "turtle",
    deduplicate: bool = True,
) -> str:
    """Merge multiple RDF files into a single knowledge graph.

    Args:
        input_files: List of paths to RDF files to merge
        output_file: Path to the output merged RDF file
        output_format: Output serialization format (turtle, n3, nt, xml, json-ld)
        deduplicate: Whether to remove duplicate triples (default: True)

    Returns:
        str: Path to the generated merged RDF file
    """
    logger.info(f"Merging {len(input_files)} RDF files into {output_file}")
    start_time = time.time()

    # Create merged graph
    merged_graph = Graph()
    merged_graph.bind("cr", "http://mlcommons.org/croissant/")
    merged_graph.bind("schema", "https://schema.org/")
    merged_graph.bind("dct", "http://purl.org/dc/terms/")

    total_triples = 0
    for i, input_file in enumerate(input_files, 1):
        file_path = Path(input_file)
        if not file_path.exists():
            logger.warning(f"File not found, skipping: {input_file}")
            continue

        logger.info(f"[{i}/{len(input_files)}] Loading {input_file}")
        file_start = time.time()

        # Parse the RDF file
        g = Graph()
        try:
            g.parse(input_file)
            triples_before = len(merged_graph)

            # Add to merged graph
            merged_graph += g

            triples_added = len(merged_graph) - triples_before
            total_triples += triples_added

            logger.info(
                f"  Loaded {len(g)} triples, added {triples_added} new triples "
                f"in {time.time() - file_start:.2f}s"
            )
        except Exception as e:
            logger.error(f"  Error parsing {input_file}: {e}")
            continue

    if deduplicate:
        logger.info("Deduplication enabled (automatic with rdflib Graph)")

    logger.info(
        f"Merged {len(input_files)} files with {len(merged_graph)} total unique triples "
        f"in {time.time() - start_time:.2f}s"
    )

    # Serialize merged graph
    logger.info(f"Writing merged graph to {output_file} in {output_format} format")
    write_start = time.time()
    merged_graph.serialize(destination=output_file, format=output_format)
    logger.info(f"Write completed in {time.time() - write_start:.2f}s")

    return output_file


def main():
    """CLI for merging RDF files from multiple providers."""
    parser = argparse.ArgumentParser(
        description="Merge RDF files from multiple Croissant providers into a single knowledge graph."
    )
    parser.add_argument(
        "input_files",
        nargs="+",
        type=str,
        help="RDF files to merge (supports wildcards like *.ttl)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        required=True,
        help="Output file path for the merged RDF",
    )
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        default="turtle",
        choices=["turtle", "n3", "nt", "xml", "json-ld"],
        help="Output serialization format (default: turtle)",
    )
    parser.add_argument(
        "--no-deduplicate",
        action="store_true",
        help="Disable deduplication of triples (faster but may have duplicates)",
    )

    args = parser.parse_args()

    # Expand wildcards and validate files
    input_files = []
    for pattern in args.input_files:
        if "*" in pattern or "?" in pattern:
            # Expand wildcard
            from glob import glob

            matched = glob(pattern)
            if matched:
                input_files.extend(matched)
            else:
                logger.warning(f"No files matched pattern: {pattern}")
        else:
            input_files.append(pattern)

    if not input_files:
        logger.error("No input files provided")
        return

    merge_rdf_files(
        input_files=input_files,
        output_file=args.output,
        output_format=args.format,
        deduplicate=not args.no_deduplicate,
    )

    print(f"Successfully merged {len(input_files)} files into: {args.output}")


if __name__ == "__main__":
    main()


__all__ = ["merge_rdf_files", "main"]
