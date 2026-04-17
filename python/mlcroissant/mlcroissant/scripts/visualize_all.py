"""Runs the Croissant visualizer on all or changed datasets."""

import os
import pathlib
import sys
from absl import app
from absl import flags
from absl import logging
from etils import epath
from mlcroissant.scripts.visualize import visualize

flags.DEFINE_string(
    "changed_files",
    None,
    "Comma-separated list of files that have changed.",
)
flags.DEFINE_boolean(
    "force",
    False,
    "Force regeneration of all visualizations.",
)
flags.DEFINE_string(
    "datasets_dir",
    "datasets",
    "Directory containing the datasets.",
)

FLAGS = flags.FLAGS


def get_all_datasets(datasets_dir_str: str):
    """Finds all metadata.json files in the datasets directory."""
    datasets = []
    # Walk through datasets_dir using pathlib
    datasets_dir = pathlib.Path(datasets_dir_str)
    for path in datasets_dir.rglob("metadata.json"):
        datasets.append(path)
    return datasets


def main(argv):
    """Main function launched by the script."""
    del argv
    
    datasets_dir = epath.Path(FLAGS.datasets_dir)
    if not datasets_dir.exists():
        logging.error(f"Datasets directory not found: {datasets_dir}")
        sys.exit(1)

    force_all = FLAGS.force
    changed_files = []
    if FLAGS.changed_files:
        changed_files = [f.strip() for f in FLAGS.changed_files.split(",")]

    # Check if the visualizer itself changed
    visualizer_files = [
        "python/mlcroissant/mlcroissant/scripts/visualize.py",
        "python/mlcroissant/mlcroissant/scripts/templates/visualizer.html",
        "python/mlcroissant/mlcroissant/scripts/visualize_all.py",
    ]
    
    for vf in visualizer_files:
        if vf in changed_files:
            logging.info(f"Visualizer file {vf} changed. Forcing full run.")
            force_all = True
            break

    all_datasets = get_all_datasets(FLAGS.datasets_dir)
    
    to_process = []
    if force_all or not FLAGS.changed_files:
        to_process = all_datasets
        logging.info(f"Processing all {len(to_process)} datasets.")
    else:
        # Incremental run
        for dataset_path in all_datasets:
            # Check if this dataset's metadata.json is in the changed files
            # We need to match the path format in changed_files (usually relative to repo root)
            # dataset_path is relative to CWD if we pass relative datasets_dir
            # Let's make it relative to repo root for comparison
            rel_path = os.path.relpath(dataset_path, os.getcwd())
            if rel_path in changed_files:
                to_process.append(dataset_path)
        
        logging.info(f"Incremental run. Processing {len(to_process)} changed datasets.")

    success_count = 0
    for dataset_path in to_process:
        output_path = dataset_path.parent / "index.html"
        logging.info(f"Generating visualization for {dataset_path} -> {output_path}")
        try:
            visualize(jsonld=str(dataset_path), output=output_path)
            success_count += 1
        except Exception as e:
            logging.error(f"Failed to visualize {dataset_path}: {e}")

    logging.info(f"Successfully visualized {success_count}/{len(to_process)} datasets.")


if __name__ == "__main__":
    app.run(main)
