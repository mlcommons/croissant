"""Main CLI entrypoint for croissant-rdf tools."""

import argparse
import sys

from croissant_rdf._src.merge_rdf import merge_rdf_command
from croissant_rdf._src.rdf_to_jsonld import rdf_to_jsonld_command


def main():
    """Main CLI entrypoint with subcommands."""
    parser = argparse.ArgumentParser(
        prog="croissant-rdf",
        description="Tools for working with RDF from Croissant JSON-LD resources.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        required=True,
    )

    # rdf-to-jsonld subcommand
    to_jsonld_parser = subparsers.add_parser(
        "to-jsonld",
        help="Convert RDF file to Croissant JSON-LD format",
        description="Convert an RDF file to JSON-LD format.",
    )
    to_jsonld_parser.add_argument(
        "rdf_file",
        type=str,
        help="Path to the RDF file (Turtle, N-Triples, RDF/XML, etc.)",
    )
    to_jsonld_parser.add_argument(
        "--output",
        "-o",
        type=str,
        required=False,
        default=None,
        help="Output JSON-LD file path (defaults to same name with .jsonld extension)",
    )
    to_jsonld_parser.set_defaults(func=rdf_to_jsonld_command)

    # merge-rdf subcommand
    merge_parser = subparsers.add_parser(
        "merge",
        help="Merge multiple RDF files into a single knowledge graph",
        description="Merge RDF files from multiple Croissant providers into a single knowledge graph.",
    )
    merge_parser.add_argument(
        "input_files",
        nargs="+",
        type=str,
        help="RDF files to merge (supports wildcards like *.ttl)",
    )
    merge_parser.add_argument(
        "--output",
        "-o",
        type=str,
        required=True,
        help="Output file path for the merged RDF",
    )
    merge_parser.add_argument(
        "--format",
        "-f",
        type=str,
        default="turtle",
        choices=["turtle", "n3", "nt", "xml", "json-ld"],
        help="Output serialization format (default: turtle)",
    )
    merge_parser.add_argument(
        "--no-deduplicate",
        action="store_true",
        help="Disable deduplication of triples (faster but may have duplicates)",
    )
    merge_parser.set_defaults(func=merge_rdf_command)

    args = parser.parse_args()

    # Execute the appropriate subcommand
    args.func(args)


if __name__ == "__main__":
    main()


__all__ = ["main"]
