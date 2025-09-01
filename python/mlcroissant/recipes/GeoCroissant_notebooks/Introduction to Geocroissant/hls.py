import os
import json
from glob import glob
import datasets

# Load Croissant metadata
with open("croissant.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

# Extract top-level metadata
_DESCRIPTION = metadata["description"]
_HOMEPAGE = metadata["url"]
_LICENSE = metadata["license"]

# Get the citation (hardcoded for now, can be made dynamic if needed)
_CITATION = """\
@software{HLS_Foundation_2023,
    author = {Phillips, Christopher and Roy, Sujit and Ankur, Kumar and Ramachandran, Rahul},
    doi    = {10.57967/hf/0956},
    month  = aug,
    title  = {{HLS Foundation Burnscars Dataset}},
    url    = {https://huggingface.co/ibm-nasa-geospatial/hls_burn_scars},
    year   = {2023}
}
"""

# Extract URL of the tar.gz (manual fallback from repo distribution)
_URLS = {
    "hls_burn_scars": {
        "archive": next(
            d["contentUrl"]
            for d in metadata["distribution"]
            if d.get("contentUrl", "").endswith(".tar.gz")
        )
    }
}


class HLSBurnScars(datasets.GeneratorBasedBuilder):
    """HLS Burn Scars dataset loader generated from Croissant metadata."""

    VERSION = datasets.Version("0.0.1")
    BUILDER_CONFIGS = [
        datasets.BuilderConfig(name="hls_burn_scars", version=VERSION, description=_DESCRIPTION),
    ]

    def _info(self):
        features = datasets.Features(
            {
                "image": datasets.Value("string"),        # <-- changed from datasets.Image()
                "annotation": datasets.Value("string"),   # <-- changed from datasets.Image()
            }
        )
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=features,
            homepage=_HOMEPAGE,
            license=_LICENSE,
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        archive_path = dl_manager.download_and_extract(_URLS["hls_burn_scars"]["archive"])

        train_path = os.path.join(archive_path, "training")
        val_path = os.path.join(archive_path, "validation")
        test_path = os.path.join(archive_path, "testing")

        splits = [
            datasets.SplitGenerator(name=datasets.Split.TRAIN, gen_kwargs={"data": train_path}),
            datasets.SplitGenerator(name=datasets.Split.VALIDATION, gen_kwargs={"data": val_path}),
        ]

        # Check if test data exists and is not empty before adding test split
        if os.path.exists(test_path) and len(os.listdir(test_path)) > 0:
            splits.append(datasets.SplitGenerator(name=datasets.Split.TEST, gen_kwargs={"data": test_path}))
        else:
            print(f"Warning: Test split folder '{test_path}' missing or empty, skipping test split.")

        return splits

    def _generate_examples(self, data):
        # Assume filename convention: *_merged.tif → .mask.tif
        files = glob(os.path.join(data, "*_merged.tif"))
        for idx, filename in enumerate(files):
            annotation_filename = filename.replace("_merged.tif", ".mask.tif")
            if os.path.exists(annotation_filename):
                yield idx, {
                    "image": filename,           # <-- now yield path string directly
                    "annotation": annotation_filename,  # <-- now yield path string directly
                }
