"""Migrates Croissant configs.

Migration from an older or non canonical Croissant format to a canonical and possibly
newer Croissant format.

## What the migration script does

- Read the current file.
- Possibly apply a custom `up` function.
- Add the `@context` defined in `mlcroissant/_src/core/json_ld.py`.
- Re-compacting back the Croissant file.

## What you have to do

- If you want to change the `@context` in Croissant files. Then change the context in
the `make_context` function in mlcroissant/_src/core/rdf.py and launch the migration:

```bash
python mlcroissant/scripts/migrations/migrate.py
```

- If you want to migrate a property in every file, you'll need to write a custom
migration function. You can do this by writing a file like
in `previous/YYYYmmddHHmm.py` (similar to previous/202307171508.py) that defines a `up`
function.

```bash
python mlcroissant/scripts/migrations/migrate.py --migration 202307171508
```

Commiting your migration allows to keep track of previous migrations in the codebase.
"""

import importlib
import json
import os

from absl import app
from absl import flags
from etils import epath

import mlcroissant as mlc
from mlcroissant._src.core.constants import DataType
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.core.json_ld import compact_jsonld
from mlcroissant._src.core.json_ld import expand_jsonld
from mlcroissant._src.datasets import Dataset
from mlcroissant._src.operation_graph.operations import Data
from mlcroissant._src.operation_graph.operations import Download
from mlcroissant._src.operation_graph.operations import Extract
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.file_object import FileObject
from mlcroissant._src.structure_graph.nodes.file_set import FileSet
from mlcroissant._src.structure_graph.nodes.metadata import Metadata
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet
from mlcroissant._src.structure_graph.nodes.source import Source

_PREVIOUS_MIGRATIONS_FOLDER = "previous"

flags.DEFINE_string(
    "migration",
    None,
    "The name of the Python file with the migration.",
)

flags.DEFINE_string(
    "version",
    "1.0",
    "The version to migrate (datasets/0.8, datasets/1.0, etc).",
)

FLAGS = flags.FLAGS


def get_migration_fn(migration: str | None):
    """Retrieves the `up` migration function from the migration file if it exists."""
    if migration is None:

        def identity_function(x):
            return x

        return identity_function
    try:
        mod = importlib.import_module(f"{_PREVIOUS_MIGRATIONS_FOLDER}.{migration}")
    except ImportError as e:
        raise ValueError(
            f"Did you create a file named {_PREVIOUS_MIGRATIONS_FOLDER}/{migration}.py?"
        ) from e
    try:
        return getattr(mod, "up")
    except AttributeError as e:
        raise ValueError(
            f"Does the file {_PREVIOUS_MIGRATIONS_FOLDER}/{migration}.py declare a `up`"
            " function?"
        ) from e


def migrate_dataset(json_ld):
    """Migrates a regular Croissant file using mlcroissant Python API."""
    metadata = mlc.Metadata.from_json(ctx=Context(), json_=json_ld)
    return metadata.to_json()


def migrate_test_dataset(dataset: epath.Path, json_ld):
    """Migrates a test Croissant files.

    Cannot use mlc.Metadata as test Croissant files may contain errors.
    """
    json_ld = compact_jsonld(expand_jsonld(json_ld))
    # Special cases for test datasets without @context
    if "recordset_missing_context_for_datatype" in os.fspath(dataset):
        del json_ld["@context"]["dataType"]
    if "mlfield_missing_source" in os.fspath(dataset):
        del json_ld["@context"]["source"]
    return json_ld


def main(argv):
    """Main function launched for the migration."""
    record_set = "images_with_bounding_box"

    # We download resources from the validation split to download smaller files.
    distribution = [
        FileObject(
            uuid="annotations_trainval2014.zip",
            name="annotations_trainval2014.zip",
            description="",
            content_url=(
                "http://images.cocodataset.org/annotations/annotations_trainval2014.zip"
            ),
            encoding_format="application/zip",
            sha256="031296bbc80c45a1d1f76bf9a90ead27e94e99ec629208449507a4917a3bf009",
        ),
        FileObject(
            uuid="annotations",
            name="annotations",
            description="",
            contained_in=["annotations_trainval2014.zip"],
            content_url="annotations/instances_val2014.json",
            encoding_format="application/json",
        ),
    ]

    # The record set has the `image_id` and the `bbox` (short for bounding box).
    record_sets = [
        RecordSet(
            uuid="images_with_bounding_box",
            name=record_set,
            fields=[
                Field(
                    uuid="images_with_bounding_box/image_id",
                    name="image_id",
                    description="",
                    data_types=DataType.INTEGER,
                    source=Source(
                        uuid="annotations",
                        node_type="fileObject",
                        extract=mlc.Extract(json_path="$.annotations[*].image_id"),
                    ),
                ),
                Field(
                    uuid="images_with_bounding_box/bbox",
                    name="bbox",
                    description="",
                    data_types=DataType.BOUNDING_BOX(Context()),
                    source=Source(
                        uuid="annotations",
                        node_type="fileObject",
                        extract=mlc.Extract(json_path="$.annotations[*].bbox"),
                    ),
                ),
            ],
        ),
    ]

    metadata = mlc.Metadata(
        name="COCO2014",
        url="https://cocodataset.org",
        distribution=distribution,
        record_sets=record_sets,
    )
    metadata.ctx.rdf.context["@base"] = "cr_base_iri/"
    jsonld = epath.Path("croissant.json")
    with jsonld.open("w") as f:
        f.write(json.dumps(metadata.to_json(), indent=2))

    dataset = Dataset(jsonld=jsonld)
    records = dataset.records(record_set=record_set)
    record = next(iter(records))
    print("The first record:")
    print(json.dumps(record, indent=2))

    # del argv
    # version = FLAGS.version
    # # Datasets in croissant/datasets
    # datasets_path = (
    #     epath.Path(__file__).parent.parent.parent.parent.parent.parent
    #     / "datasets"
    #     / version
    # )
    # datasets = [path for path in datasets_path.glob("*/*.json")]
    # assert datasets, f"No dataset found in {datasets_path}"
    # # Datasets in croissant/python/mlcroissant/_src/tests
    # test_path = (
    #     epath.Path(__file__).parent.parent.parent.parent
    #     / "mlcroissant/_src/tests/graphs"
    #     / version
    # )
    # test_datasets = [
    #     p
    #     for p in test_path.glob("*/*.json")
    #     if not os.fspath(p).endswith("recordset_bad_type/metadata.json")
    # ]
    # assert test_datasets, f"No dataset found in {test_path}"
    # for dataset in datasets:
    #     print(f"Converting {dataset}...")
    #     with dataset.open("r") as f:
    #         json_ld = json.load(f)
    #         up = get_migration_fn(FLAGS.migration)
    #         json_ld = up(json_ld)
    #     json_ld = migrate_dataset(json_ld)
    #     with dataset.open("w") as f:
    #         json.dump(json_ld, f, indent="  ")
    #         f.write("\n")
    # for dataset in test_datasets:
    #     print(f"Converting test dataset {dataset}...")
    #     with dataset.open("r") as f:
    #         json_ld = json.load(f)
    #         up = get_migration_fn(FLAGS.migration)
    #         json_ld = up(json_ld)
    #     json_ld = migrate_test_dataset(dataset, json_ld)
    #     with dataset.open("w") as f:
    #         json.dump(json_ld, f, indent="  ")
    #         f.write("\n")
    # print("Done.")


if __name__ == "__main__":
    app.run(main)
