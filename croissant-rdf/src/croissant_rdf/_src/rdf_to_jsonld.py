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

    converter = RDFConverter()
    output_file = converter.convert_from_rdf(args.rdf_file)

    if args.output:
        import shutil

        shutil.move(output_file, args.output)
        output_file = args.output

    print(f"Successfully converted to: {output_file}")


if __name__ == "__main__":
    main()


__all__ = ["RDFConverter", "main"]
