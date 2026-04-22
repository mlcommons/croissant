"""JS-driven Croissant visualizer.

Parallel implementation alongside visualize.py.  Instead of Jinja2 rendering
a full monolithic HTML page, this script:

  1. Augments the raw Croissant JSON-LD with ``cr:examples`` preview data.
  2. Writes a minimal HTML shell that embeds the augmented JSON-LD as
     ``window.__CROISSANT_DATA__``.
  3. Copies ``static/visualizer.js`` and ``static/visualizer.css`` next to
     the output HTML file so the page can load them with relative paths.

Usage (standalone)::

    python -m mlcroissant.scripts.visualize_js \
        --jsonld datasets/0.8/titanic/metadata.json \
        --output datasets/0.8/titanic/index-js.html
"""

import copy
import json
import pathlib
import shutil
import sys
from typing import Any

from absl import logging
from etils import epath
import jinja2

import mlcroissant as mlc

# Re-use all helper functions from the existing visualizer.
from mlcroissant.scripts.visualize import (
    _get_or_generate_recordset_preview,
    _resolve_fileset_files,
)

# Directory containing static assets (visualizer.js, visualizer.css)
_STATIC_DIR = pathlib.Path(__file__).parent / "static"
_TEMPLATES_DIR = pathlib.Path(__file__).parent / "templates"

_MAX_PREVIEW_FILES = 10


def _augment_distribution(
    dist_entry: dict,
    metadata_distribution: list,
    folder: epath.Path | None,
) -> dict:
    """Add ``cr:examples`` to a distribution JSON-LD entry.

    For FileObjects with a local text/CSV content URL, embeds a text preview.
    For FileSets, embeds the resolved file listing from the parent archive.
    Does not modify the original dict.
    """
    entry = copy.copy(dist_entry)
    res_type = ""
    t = dist_entry.get("@type", "")
    if isinstance(t, list):
        t = " ".join(t)
    if "FileObject" in t or t == "sc:FileObject":
        res_type = "FileObject"
    elif "FileSet" in t or t == "sc:FileSet":
        res_type = "FileSet"

    if res_type == "FileObject" and folder:
        content_url = dist_entry.get("contentUrl", "")
        if content_url and not str(content_url).startswith("http"):
            file_path = folder / content_url
            if file_path.exists():
                enc_fmts = dist_entry.get("encodingFormat", [])
                if isinstance(enc_fmts, str):
                    enc_fmts = [enc_fmts]
                if enc_fmts and any(
                    fmt in ["text/csv", "text/plain"] for fmt in enc_fmts
                ):
                    try:
                        with file_path.open("r") as f:
                            text_preview = "".join(
                                [f.readline() for _ in range(5)]
                            )
                        entry["cr:examples"] = {"text_preview": text_preview}
                    except Exception as e:
                        logging.warning(
                            f"Could not read preview for {dist_entry.get('name')}: {e}"
                        )

    if res_type == "FileSet" and folder:
        # We need an mlcroissant resource object to resolve the fileset.
        # Find the matching resource from metadata.distribution.
        name = dist_entry.get("name") or dist_entry.get("@id") or ""
        matching_res = None
        for res in metadata_distribution:
            if res.name == name or res.uuid == name:
                matching_res = res
                break
        if matching_res is not None:
            file_list, file_count = _resolve_fileset_files(
                matching_res, metadata_distribution, folder
            )
            includes = list(getattr(matching_res, "includes", []) or [])
            entry["cr:examples"] = {
                "file_list": file_list,
                "file_count": file_count,
                "includes": includes,
            }

    return entry


def _augment_record_set(
    rs_entry: dict,
    dataset: mlc.Dataset,
    folder: epath.Path | None,
) -> dict:
    """Add ``cr:examples`` to a record set JSON-LD entry with preview data."""
    entry = copy.copy(rs_entry)
    rs_name = rs_entry.get("name") or rs_entry.get("@id") or ""
    if not rs_name:
        return entry
    preview_cols, preview_rows = _get_or_generate_recordset_preview(
        dataset, rs_name, folder
    )
    if preview_cols and preview_rows:
        entry["cr:examples"] = {
            "columns": preview_cols,
            "rows": preview_rows,
        }
    return entry


def visualize_js(jsonld: str, output: epath.Path) -> None:
    """Generate a JS-driven visualization HTML page for a Croissant dataset."""
    logging.info(f"Loading dataset from {jsonld}")
    try:
        dataset = mlc.Dataset(jsonld)
    except Exception as e:
        logging.error(f"Failed to load dataset: {e}")
        sys.exit(1)

    metadata = dataset.metadata
    folder: epath.Path | None = metadata.ctx.folder

    # Load raw JSON-LD
    jsonld_path = epath.Path(jsonld)
    try:
        raw_jsonld: dict[str, Any] = json.loads(jsonld_path.read_text())
    except Exception:
        raw_jsonld = {}

    # Deep-copy so we can augment without mutating the original
    augmented = copy.deepcopy(raw_jsonld)

    # Augment distributions with cr:examples
    distributions = augmented.get("distribution", [])
    if not isinstance(distributions, list):
        distributions = [distributions]
    augmented_dists = [
        _augment_distribution(d, metadata.distribution, folder)
        for d in distributions
    ]
    augmented["distribution"] = augmented_dists

    # Augment record sets with cr:examples
    record_sets = augmented.get("recordSet", [])
    if not isinstance(record_sets, list):
        record_sets = [record_sets]
    augmented_rs = [
        _augment_record_set(rs, dataset, folder) for rs in record_sets
    ]
    augmented["recordSet"] = augmented_rs

    # Render HTML shell
    loader = jinja2.FileSystemLoader(_TEMPLATES_DIR)
    env = jinja2.Environment(
        loader=loader, autoescape=jinja2.select_autoescape()
    )
    template = env.get_template("visualizer_js.html")
    data_json = json.dumps(augmented, indent=2, ensure_ascii=False)
    html = template.render(
        name=metadata.name or "Dataset",
        data_json=data_json,
    )
    output.write_text(html)
    print(f"Wrote JS visualization to {output}")

    # Copy static assets next to the output file
    output_dir = pathlib.Path(str(output)).parent
    for asset in ("visualizer.js", "visualizer.css"):
        src = _STATIC_DIR / asset
        dst = output_dir / asset
        if src.exists():
            shutil.copy(src, dst)
            logging.info(f"Copied {src} -> {dst}")
        else:
            logging.warning(f"Static asset not found: {src}")


def main(argv: list | None = None) -> None:
    """Entry point when run as a standalone script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a JS-driven Croissant visualizer HTML page."
    )
    parser.add_argument(
        "--jsonld", required=True, help="Path to the Croissant JSON-LD file."
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output HTML file (default: index.html next to the JSON-LD).",
    )
    args = parser.parse_args(argv)
    jsonld = args.jsonld
    if args.output:
        output = epath.Path(args.output)
    else:
        output = epath.Path(jsonld).parent / "index.html"
    visualize_js(jsonld=jsonld, output=output)


if __name__ == "__main__":
    main()
