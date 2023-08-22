"""Example script to serialize a Python metadata to JSON-LD."""

import json

from absl import app
from absl import logging

import ml_croissant as mlc


def main(argv):
    """Main function launched by the script."""
    del argv
    metadata = mlc.nodes.Metadata(
        name="my-new-dataset",
        description="This is a new dataset.",
        url="https://mlcommons.org/dataset",
        file_objects=[
            mlc.nodes.FileObject(
                name="source_csv",
                description="The source CSV.",
                content_url="https://mlcommons.org/dataset.csv",
            )
        ],
        record_sets=[
            mlc.nodes.RecordSet(
                name="default",
                description="The default set of records in the dataset.",
                fields=[
                    mlc.nodes.Field(
                        name="column_name", description="This is a dataset field"
                    )
                ],
            )
        ],
    )
    # Check if there are errors:
    if metadata.issues.errors:
        logging.error(metadata.issues.report())
    # Serialize to JSON-LD:
    json_ = metadata.to_json()
    print(json.dumps(json_, indent=2))


if __name__ == "__main__":
    app.run(main)
