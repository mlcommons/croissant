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


def _standardize_dataset(
    dataset: str,
) -> tuple[str, list[datasets.DatasetBuilder]]:
    """Standardizes the user input `--dataset` to a tuple (URL, builder, configs)."""
    if dataset.startswith(_HUGGING_FACE_URL):
        url, dataset_name = dataset, dataset.replace(_HUGGING_FACE_URL, "")
    else:
        url, dataset_name = _HUGGING_FACE_URL + dataset, dataset
    configs = datasets.get_dataset_config_names(dataset_name)
    if not configs:
        builder = datasets.load_dataset_builder(dataset_name)
        return url, [builder]
    else:
        builders = [
            datasets.load_dataset_builder(dataset_name, config) for config in configs
        ]
        return url, builders


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


def _get_record_sets(
    builders: list[datasets.DatasetBuilder],
) -> list[mlc.nodes.RecordSet]:
    record_sets: list[mlc.nodes.RecordSet] = []
    for builder in builders:
        name = builder.config.name if len(builders) > 1 else "default"
        fields = _get_fields(builder)
        record_sets.append(
            mlc.nodes.RecordSet(
                name=name,
                description=f"The {name} set of records in the dataset.",
                fields=fields,
            )
        )
    return record_sets


def convert(dataset: str) -> dict[str, Any]:
    """Converts from Hugging Face to Croissant JSON-LD."""
    dataset_url, builders = _standardize_dataset(dataset)
    record_sets = _get_record_sets(builders)
    metadata = mlc.nodes.Metadata(
        name=builders[0].name,
        citation=builders[0].info.citation,
        license=builders[0].info.license,
        description=builders[0].info.description,
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
                # Without config (mnist), the file structure is: mnist/train/000.parquet
                # With config (c4), the file structure is: en/train/000.parquet
                includes="*/*/*.parquet",
            )
        ],
        record_sets=record_sets,
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
