"""Migrates Croissant configs from an older or non canonical Croissant format to a
canonical and possibly newer Croissant format."""

import json

from etils import epath
from ml_croissant._src.core.json_ld import expand_json_ld, reduce_json_ld

if __name__ == "__main__":
    datasets = [
        path for path in epath.Path("../../datasets").glob("*titanic*/metadata.json")
    ]
    for dataset in datasets:
        print(f"Converting {dataset}...")
        with dataset.open("r") as f:
            json_ld = json.load(f)
            json_ld = reduce_json_ld(expand_json_ld(json_ld))
        with dataset.open("w") as f:
            json.dump(json_ld, f, indent="  ")
            f.write("\n")
    print("Done.")
