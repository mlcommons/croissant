"""Migrates Croissant configs.

Migration from an older or non canonical Croissant format to a canonical and possibly
newer Croissant format.
"""

import json

from etils import epath
from ml_croissant._src.core.json_ld import expand_json_ld, compact_json_ld

if __name__ == "__main__":
    # Datasets in croissant/datasets
    datasets = [path for path in epath.Path("../../datasets").glob("*/*.json")]
    # Datasets in croissant/python/ml_croissant/_src/tests
    datasets += [
        path for path in epath.Path("ml_croissant/_src/tests/graphs").glob("*.json")
    ]
    for dataset in datasets:
        print(f"Converting {dataset}...")
        with dataset.open("r") as f:
            json_ld = json.load(f)
            json_ld = compact_json_ld(expand_json_ld(json_ld))
        with dataset.open("w") as f:
            # Special cases for test datasets without @context
            if dataset.name == "recordset_missing_context_for_datatype.json":
                del json_ld["@context"]["dataType"]
            if dataset.name == "mlfield_missing_source.json":
                del json_ld["@context"]["source"]
            json.dump(json_ld, f, indent="  ")
            f.write("\n")
    print("Done.")
