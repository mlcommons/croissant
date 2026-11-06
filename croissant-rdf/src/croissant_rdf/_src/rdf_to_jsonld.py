"""Convert RDF files back to Croissant JSON-LD format."""

import argparse

from croissant_rdf._src.croissant_harvester import CroissantHarvester


class RDFConverter(CroissantHarvester):
    """Converter for RDF to JSON-LD without requiring provider-specific logic."""

    def fetch_datasets_ids(self):
        """Not used for RDF conversion."""
        return []

    def fetch_dataset_croissant(self, dataset_id: str):
        """Not used for RDF conversion."""
        pass


def rdf_to_jsonld_command(args):
    """Execute the RDF to JSON-LD conversion command.

    Args:
        args: Parsed command-line arguments with rdf_file and output attributes.
    """
    converter = RDFConverter()
    output_file = converter.convert_from_rdf(args.rdf_file)

    if args.output:
        import shutil

        shutil.move(output_file, args.output)
        output_file = args.output

    print(f"Successfully converted to: {output_file}")


def main():
    """Convert an RDF file to JSON-LD format."""
    parser = argparse.ArgumentParser(description="Convert RDF file to Croissant JSON-LD format.")
    parser.add_argument(
        "rdf_file",
        type=str,
        help="Path to the RDF file (Turtle, N-Triples, RDF/XML, etc.)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        required=False,
        default=None,
        help="Output JSON-LD file path (defaults to same name with .jsonld extension)",
    )
    args = parser.parse_args()
    rdf_to_jsonld_command(args)


if __name__ == "__main__":
    main()


__all__ = ["RDFConverter", "rdf_to_jsonld_command", "main"]
