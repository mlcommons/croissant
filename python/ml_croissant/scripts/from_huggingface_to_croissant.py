"""Converts Hugging Face datasets to Croissant JSON-LD files.

Usage:

```
python scripts/convert_from_huggingface.py --dataset mnist
```
"""

import json
import os
import tempfile
import time
from typing import Any

from absl import app
from absl import flags
from absl import logging
import datasets
from etils import epath

import ml_croissant as mlc

flags.DEFINE_string(
    "dataset",
    None,
    "Dataset name or URL on huggingface.co/datasets.",
)

flags.DEFINE_string(
    "output",
    None,
    "Dataset name or URL on huggingface.co/datasets.",
)

flags.mark_flag_as_required("dataset")

_HUGGING_FACE_URL = "https://huggingface.co/datasets/"
_REPO = "repo"
_PARQUET_FILES = "parquet-files"

FLAGS = flags.FLAGS


def _standardize_dataset(dataset: str) -> tuple[str, datasets.DatasetBuilder]:
    """Standardizes the user input `--dataset` to a tuple (URL, builder)."""
    if dataset.startswith(_HUGGING_FACE_URL):
        url, dataset_name = dataset, dataset.replace(_HUGGING_FACE_URL, "")
    else:
        url, dataset_name = _HUGGING_FACE_URL + dataset, dataset
    builder = datasets.load_dataset_builder(dataset_name)
    return url, builder


def _standardize_output(output: str | None) -> epath.Path:
    """Standardizes the user input `--output` to a file path."""
    if output is None:
        return epath.Path(tempfile.gettempdir()) / f"croissant_{time.time()}.json"
    else:
        return epath.Path(output).expanduser()


def _get_data_type(feature: datasets.Features) -> str:
    """Gets Croissant data type from Hugging Face data type."""
    feature_type = feature.dtype
    if feature_type == "string":
        return "sc:Text"
    elif feature_type == "bool":
        return "sc:Boolean"
    elif feature_type == "float":
        return "sc:Float"
    elif feature_type in ["int32", "int64"]:
        return "sc:Integer"
    else:
        raise ValueError(f"Cannot convert the feature {feature} to Croissant.")


def _get_fields(builder: datasets.DatasetBuilder) -> list[mlc.nodes.Field]:
    """Lists fields from Hugging Face features."""
    features = builder.info.features
    fields: list[mlc.nodes.Field] = []
    for name, feature in features.items():
        try:
            data_type = _get_data_type(feature)
        except ValueError as exception:
            logging.error(exception)
            continue
        fields.append(
            mlc.nodes.Field(
                name=name,
                description="Column from Hugging Face parquet file.",
                data_type=data_type,
                source=mlc.nodes.Source(
                    uid=_PARQUET_FILES,
                    node_type="distribution",
                    extract=mlc.nodes.Extract(csv_column=name),
                ),
            )
        )
    return fields


def convert(dataset: str) -> dict[str, Any]:
    """Converts from Hugging Face to Croissant JSON-LD."""
    dataset_url, dataset_builder = _standardize_dataset(dataset)
    fields = _get_fields(dataset_builder)
    metadata = mlc.nodes.Metadata(
        name=dataset_builder.name,
        citation=dataset_builder.info.citation,
        license=dataset_builder.info.license,
        description=dataset_builder.info.description,
        url=dataset_url,
        file_objects=[
            mlc.nodes.FileObject(
                name=_REPO,
                description="The Hugging Face git repository.",
                content_url=dataset_url + "/tree/refs%2Fconvert%2Fparquet",
                encoding_format="git+https",
                sha256="https://github.com/mlcommons/croissant/issues/80",
            )
        ],
        file_sets=[
            mlc.nodes.FileSet(
                name=_PARQUET_FILES,
                description=(
                    "The underlying Parquet files as converted by Hugging Face (see:"
                    " https://huggingface.co/docs/datasets-server/parquet)."
                ),
                contained_in=[_REPO],
                encoding_format="application/x-parquet",
                includes=dataset_builder.name + "/*/*.parquet",
            )
        ],
        record_sets=[
            mlc.nodes.RecordSet(
                name="default",
                description="The default set of records in the dataset.",
                fields=fields,
            )
        ],
    )
    # Serialize to JSON-LD:
    return metadata.to_json()


def main(argv):
    """Main function launched by the script."""
    del argv
    dataset = FLAGS.dataset
    output = FLAGS.output
    output = _standardize_output(output)
    jsonld = convert(dataset)
    with output.open("w") as f:
        f.write(json.dumps(jsonld, indent=2))
        f.write("\n")
    logging.info("Done. Wrote Croissant JSON-LD to %s", os.fspath(output))


if __name__ == "__main__":
    app.run(main)
