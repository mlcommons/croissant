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
mlcroissant/_src/core/json_ld.py and launch the migration:

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
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.json_ld import compact_jsonld
from mlcroissant._src.core.json_ld import expand_jsonld

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
    del argv
    version = FLAGS.version
    # Datasets in croissant/datasets
    datasets_path = (
        epath.Path(__file__).parent.parent.parent.parent.parent.parent
        / "datasets"
        / version
    )
    datasets = [path for path in datasets_path.glob("*/*.json")]
    assert datasets, f"No dataset found in {datasets_path}"
    # Datasets in croissant/python/mlcroissant/_src/tests
    test_path = (
        epath.Path(__file__).parent.parent.parent.parent
        / "mlcroissant/_src/tests/graphs"
        / version
    )
    test_datasets = [
        p
        for p in test_path.glob("*/*.json")
        if not os.fspath(p).endswith("recordset_bad_type/metadata.json")
    ]
    assert test_datasets, f"No dataset found in {test_path}"
    for dataset in datasets:
        print(f"Converting {dataset}...")
        with dataset.open("r") as f:
            json_ld = json.load(f)
            up = get_migration_fn(FLAGS.migration)
            json_ld = up(json_ld)
        json_ld = migrate_dataset(json_ld)
        with dataset.open("w") as f:
            json.dump(json_ld, f, indent="  ")
            f.write("\n")
    for dataset in test_datasets:
        print(f"Converting test dataset {dataset}...")
        with dataset.open("r") as f:
            json_ld = json.load(f)
            up = get_migration_fn(FLAGS.migration)
            json_ld = up(json_ld)
        json_ld = migrate_test_dataset(dataset, json_ld)
        with dataset.open("w") as f:
            json.dump(json_ld, f, indent="  ")
            f.write("\n")
    print("Done.")


if __name__ == "__main__":
    app.run(main)
