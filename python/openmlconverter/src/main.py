"""Fetch an OpenML Dataset, and convert it into DCF (Croissant) format.

Typical usage:
    python3 src/main.py --id [openml-id] --output [your-output-dir]
"""

import argparse
import json
import logging
import pathlib

import converter
import fetch_openml
from serialization import serialize_dcf_json_field


def _parse_args() -> argparse.Namespace:
    """Parse the command line arguments.

    Returns:
         The argument Namespace filled with the values.
    """
    parser = argparse.ArgumentParser(description="Please refer to the README.")
    parser.add_argument("--id", required=True, help="OpenML dataset identifier to convert")
    parser.add_argument("-o", "--output", required=True, help="Output folder")
    return parser.parse_args()


def main():
    """Read command line arguments, fetch an OpenML dataset, convert it into DCF (Croissant)
    format, and write the result to files.

    Resulting file:
        [output-folder]/[openml-id].json
    The output-folder and openml-id are both command line arguments.
    """
    logging.basicConfig(encoding="utf-8", level=logging.INFO)
    args = _parse_args()
    openml_id = args.id
    output_folder = pathlib.Path(args.output)

    output_folder.mkdir(parents=True, exist_ok=True)
    dcf = convert(openml_id)
    output_filepath = output_folder / f"{openml_id}.json"
    with open(output_filepath, "w") as f:
        json.dump(dcf, f, default=serialize_dcf_json_field)
        logging.info(f"Result written to {output_filepath.resolve()}")


def convert(openml_id) -> dict:
    """Fetch an OpenML dataset, and convert it into DCF (Croissant) format.

    Args:
        openml_id: the identifier of an OpenML Dataset.

    Returns:
        A dictionary containing the DCF representation of the Dataset.
    """
    dataset_json = fetch_openml.dataset_json(openml_id)
    features_json = fetch_openml.features_json(openml_id)
    dcf = converter.convert(dataset_json, features_json)
    return dcf


if __name__ == "__main__":
    main()
