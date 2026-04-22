"""Runs the Croissant visualizer on all or changed datasets."""

import os
import pathlib
import sys

from absl import app
from absl import flags
from absl import logging
import csscompressor  # type: ignore
from etils import epath
import jsmin  # type: ignore

from mlcroissant.scripts.visualize import visualize_js

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
flags.DEFINE_string(
    "static_dir",
    None,
    "Directory to copy static assets to. Defaults to <datasets_dir>/static.",
)

FLAGS = flags.FLAGS

# Files that, when changed, trigger a full regeneration of all datasets.
_VISUALIZER_FILES = [
    "python/mlcroissant/mlcroissant/scripts/visualize.py",
    "python/mlcroissant/mlcroissant/scripts/visualize_utils.py",
    "python/mlcroissant/mlcroissant/scripts/templates/visualizer.html",
    "python/mlcroissant/mlcroissant/scripts/static/visualizer.js",
    "python/mlcroissant/mlcroissant/scripts/static/visualizer.css",
    "python/mlcroissant/mlcroissant/scripts/visualize_all.py",
]


def get_all_datasets(datasets_dir_str: str):
    """Finds all metadata.json files in the datasets directory."""
    datasets = []
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

    # Any change to a visualizer source file triggers a full rebuild.
    for vf in _VISUALIZER_FILES:
        if vf in changed_files:
            logging.info(f"Visualizer file {vf} changed. Forcing full run.")
            force_all = True
            break

    all_datasets = get_all_datasets(FLAGS.datasets_dir)

    # Minify and copy static assets once to the shared location
    static_src_dir = pathlib.Path(__file__).parent / "static"
    if FLAGS.static_dir:
        static_dst_dir = pathlib.Path(FLAGS.static_dir)
    else:
        static_dst_dir = pathlib.Path(FLAGS.datasets_dir) / "static"
    try:
        static_dst_dir.mkdir(parents=True, exist_ok=True)

        # Minify JS
        js_src = (static_src_dir / "visualizer.js").read_text(encoding="utf-8")
        js_min = jsmin.jsmin(js_src)
        (static_dst_dir / "visualizer.min.js").write_text(js_min, encoding="utf-8")

        # Minify CSS
        css_src = (static_src_dir / "visualizer.css").read_text(encoding="utf-8")
        css_min = csscompressor.compress(css_src)
        (static_dst_dir / "visualizer.min.css").write_text(css_min, encoding="utf-8")

        logging.info(f"Minified and copied static assets to {static_dst_dir}")
    except Exception as e:
        logging.error(f"Failed to minify static assets: {e}")
        sys.exit(1)

    to_process = []
    if force_all or not FLAGS.changed_files:
        to_process = all_datasets
        logging.info(f"Processing all {len(to_process)} datasets.")
    else:
        # Incremental run: only regenerate datasets whose metadata.json changed.
        for dataset_path in all_datasets:
            rel_path = os.path.relpath(dataset_path, os.getcwd())
            if rel_path in changed_files:
                to_process.append(dataset_path)
        logging.info(f"Incremental run. Processing {len(to_process)} changed datasets.")

    success_count = 0
    for dataset_path in to_process:
        output_path = dataset_path.parent / "index.html"
        # Calculate relative path to shared static assets
        static_path = os.path.relpath(static_dst_dir, output_path.parent)
        logging.info(
            f"Generating visualization for {dataset_path} -> {output_path} using"
            f" static_path={static_path}"
        )
        try:
            visualize_js(
                jsonld=str(dataset_path), output=output_path, static_path=static_path
            )
            success_count += 1
        except Exception as e:
            logging.error(f"Failed to visualize {dataset_path}: {e}")

    logging.info(f"Successfully visualized {success_count}/{len(to_process)} datasets.")


if __name__ == "__main__":
    app.run(main)
