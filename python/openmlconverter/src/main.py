import argparse
import json
import logging
import pathlib

import converter
import fetch_openml
from serialization import serialize_json


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Please refer to the README.")
    parser.add_argument("--id", required=True, help="OpenML dataset identifier to convert")
    parser.add_argument("-o", "--output", required=True, help="Output folder")
    return parser.parse_args()


def main():
    logging.basicConfig(encoding="utf-8", level=logging.INFO)
    args = _parse_args()
    openml_id = args.id
    output_folder = pathlib.Path(args.output)

    output_folder.mkdir(parents=True, exist_ok=True)
    croissant = convert(openml_id)
    output_filepath = output_folder / f"{openml_id}.json"
    with open(output_filepath, "w") as f:
        json.dump(croissant, f, default=serialize_json, sort_keys=True)
        logging.info(f"Result written to {output_filepath.resolve()}")


def convert(openml_id):
    dataset_json = fetch_openml.dataset_json(openml_id)
    features_json = fetch_openml.features_json(openml_id)
    croissant = converter.bake(dataset_json, features_json)
    return croissant


if __name__ == "__main__":
    main()
