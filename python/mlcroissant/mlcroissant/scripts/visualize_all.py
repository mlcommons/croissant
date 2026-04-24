"""Runs the Croissant visualizer on all or changed datasets."""

import datetime
import json
import os
import pathlib
import re
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
    "python/mlcroissant/mlcroissant/scripts/templates/gallery.html",
    "python/mlcroissant/mlcroissant/scripts/static/visualizer.js",
    "python/mlcroissant/mlcroissant/scripts/static/visualizer.css",
    "python/mlcroissant/mlcroissant/scripts/static/gallery.js",
    "python/mlcroissant/mlcroissant/scripts/static/gallery.css",
    "python/mlcroissant/mlcroissant/scripts/visualize_all.py",
]

_STATIC_SRC_DIR = pathlib.Path(__file__).parent / "static"
_TEMPLATES_DIR = pathlib.Path(__file__).parent / "templates"


def get_all_datasets(datasets_dir_str: str):
    """Finds all metadata.json files in the datasets directory."""
    datasets = []
    datasets_dir = pathlib.Path(datasets_dir_str)
    for path in datasets_dir.rglob("metadata.json"):
        datasets.append(path)
    return datasets


# ── Gallery index helpers ──────────────────────────────────────────────────────


def _schema_version_from_conforms_to(conforms_to: str | None) -> str | None:
    """Extract a short version label like '1.0' from a conformsTo URL."""
    if not conforms_to:
        return None
    m = re.search(r"(\d+\.\d+(?:\.\d+)?)$", str(conforms_to))
    return m.group(1) if m else None


def _version_sort_key(label: str) -> tuple:
    """Sort version labels numerically descending (newest first)."""
    try:
        parts = tuple(int(x) for x in label.split("."))
    except ValueError:
        parts = (0,)
    # Negate for descending order
    return tuple(-p for p in parts)


def _build_dataset_entry(
    metadata_path: pathlib.Path,
    datasets_dir: pathlib.Path,
) -> dict | None:
    """Build a lightweight index entry for one dataset.

    Reads only the metadata.json (no data files, no mlcroissant loading).
    Returns None if the file cannot be parsed.
    """
    try:
        raw = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception as e:
        logging.warning(f"Could not parse {metadata_path}: {e}")
        return None

    name = raw.get("name") or ""
    if not name:
        logging.warning(f"Skipping {metadata_path}: no 'name' field.")
        return None

    description = raw.get("description") or ""
    # Truncate for the snippet
    if len(description) > 240:
        description = description[:237].rstrip() + "…"

    conforms_to = raw.get("conformsTo") or ""
    version_label = _schema_version_from_conforms_to(conforms_to)

    # Fallback: infer schema version from directory structure
    if not version_label:
        rel = metadata_path.relative_to(datasets_dir)
        parts = rel.parts
        if parts and re.match(r"^\d+\.\d+", parts[0]):
            version_label = parts[0]

    keywords = raw.get("keywords") or []
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]

    distributions = raw.get("distribution") or []
    if not isinstance(distributions, list):
        distributions = [distributions]
    record_sets = raw.get("recordSet") or []
    if not isinstance(record_sets, list):
        record_sets = [record_sets]

    # Path to the generated index.html, relative to datasets/index.html
    index_html = metadata_path.parent / "index.html"
    rel_path = os.path.relpath(index_html, datasets_dir)
    # Normalise to forward slashes for HTML hrefs
    rel_path = rel_path.replace(os.sep, "/")

    # Slug: unique identifier for anchors / sidebar links
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

    return {
        "name": name,
        "slug": slug,
        "path": rel_path,
        "description": description,
        "version": raw.get("version") or "",
        "conformsTo": conforms_to,
        "license": raw.get("license") or "",
        "url": raw.get("url") or "",
        "keywords": keywords,
        "num_resources": len(distributions),
        "num_record_sets": len(record_sets),
        "_schema_version": version_label or "unknown",
    }


def build_gallery_index(
    all_datasets: list[pathlib.Path],
    datasets_dir: pathlib.Path,
    static_dst_dir: pathlib.Path,
) -> None:
    """Build datasets/index.html — the central dataset gallery page."""
    entries = []
    for metadata_path in all_datasets:
        entry = _build_dataset_entry(metadata_path, datasets_dir)
        if entry:
            entries.append(entry)

    # Group by schema version
    versions_map: dict[str, list[dict]] = {}
    for entry in entries:
        v = entry["_schema_version"]
        versions_map.setdefault(v, []).append(entry)

    # Sort versions descending (newest first), datasets alphabetically within each
    sorted_versions = sorted(versions_map.keys(), key=_version_sort_key)
    versions_list = []
    for v_label in sorted_versions:
        group = sorted(versions_map[v_label], key=lambda d: d["name"].lower())
        # Find representative conformsTo URL for the section header link
        conforms_to_url = next((d["conformsTo"] for d in group if d["conformsTo"]), "")
        # Strip internal _schema_version helper key before serialising
        clean_group = [
            {k: val for k, val in d.items() if k != "_schema_version"} for d in group
        ]
        versions_list.append({
            "label": v_label,
            "conformsTo": conforms_to_url,
            "datasets": clean_group,
        })

    readme_path = datasets_dir / "README.md"
    readme_intro = ""
    readme_rest = ""
    if readme_path.exists():
        readme_content = readme_path.read_text(encoding="utf-8")
        paragraphs = readme_content.split("\n\n")
        # Filter out header lines to find the first actual paragraph
        non_header_paragraphs = [p for p in paragraphs if not p.strip().startswith("#")]
        if non_header_paragraphs:
            readme_intro = non_header_paragraphs[0].strip()
            # Find the index of the intro paragraph to split the rest
            intro_idx = paragraphs.index(non_header_paragraphs[0])
            readme_rest = "\n\n".join(paragraphs[intro_idx + 1 :])
        else:
            if paragraphs:
                readme_intro = paragraphs[0].strip()
                readme_rest = "\n\n".join(paragraphs[1:])

    gallery_data = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "versions": versions_list,
        "readme_intro": readme_intro,
        "readme_rest": readme_rest,
    }

    # Compute relative path from datasets/ to static/
    static_path = os.path.relpath(static_dst_dir, datasets_dir).replace(os.sep, "/")

    # Inject data + static paths into the gallery HTML shell
    data_script = (
        "<script>window.__GALLERY_DATA__ = "
        + json.dumps(gallery_data, indent=2, ensure_ascii=False)
        + ";</script>"
    )
    template_html = (_TEMPLATES_DIR / "gallery.html").read_text(encoding="utf-8")
    html = template_html.replace("<!-- GALLERY_DATA -->", data_script)
    html = html.replace("STATIC_PATH", static_path)

    output = datasets_dir / "index.html"
    output.write_text(html, encoding="utf-8")
    logging.info(f"Wrote gallery index to {output} ({len(entries)} datasets)")


# ── Main ──────────────────────────────────────────────────────────────────────


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
    if FLAGS.static_dir:
        static_dst_dir = pathlib.Path(FLAGS.static_dir)
    else:
        static_dst_dir = pathlib.Path(FLAGS.datasets_dir) / "static"
    try:
        static_dst_dir.mkdir(parents=True, exist_ok=True)

        # Minify visualizer JS + CSS
        js_src = (_STATIC_SRC_DIR / "visualizer.js").read_text(encoding="utf-8")
        js_min = jsmin.jsmin(js_src)
        (static_dst_dir / "visualizer.min.js").write_text(js_min, encoding="utf-8")

        css_src = (_STATIC_SRC_DIR / "visualizer.css").read_text(encoding="utf-8")
        css_min = csscompressor.compress(css_src)
        (static_dst_dir / "visualizer.min.css").write_text(css_min, encoding="utf-8")

        # Minify gallery JS + CSS
        gallery_js_src = (_STATIC_SRC_DIR / "gallery.js").read_text(encoding="utf-8")
        gallery_js_min = jsmin.jsmin(gallery_js_src)
        (static_dst_dir / "gallery.min.js").write_text(gallery_js_min, encoding="utf-8")

        gallery_css_src = (_STATIC_SRC_DIR / "gallery.css").read_text(encoding="utf-8")
        gallery_css_min = csscompressor.compress(gallery_css_src)
        (static_dst_dir / "gallery.min.css").write_text(
            gallery_css_min, encoding="utf-8"
        )

        logging.info(f"Minified and copied static assets to {static_dst_dir}")
    except Exception as e:
        logging.error(f"Failed to minify static assets: {e}")
        sys.exit(1)

    # Build the gallery index (always, even on incremental runs — it's cheap)
    build_gallery_index(
        all_datasets=all_datasets,
        datasets_dir=pathlib.Path(FLAGS.datasets_dir),
        static_dst_dir=static_dst_dir,
    )

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

    # Compute the gallery index path for the back-link
    gallery_index = pathlib.Path(FLAGS.datasets_dir) / "index.html"

    success_count = 0
    for dataset_path in to_process:
        output_path = dataset_path.parent / "index.html"
        # Calculate relative path to shared static assets
        static_path = os.path.relpath(static_dst_dir, output_path.parent)
        # Calculate relative path back to gallery index (for the "← All Datasets" link)
        gallery_url = os.path.relpath(gallery_index, output_path.parent).replace(
            os.sep, "/"
        )
        logging.info(
            f"Generating visualization for {dataset_path} -> {output_path} using"
            f" static_path={static_path}"
        )
        try:
            visualize_js(
                jsonld=str(dataset_path),
                output=output_path,
                static_path=static_path,
                gallery_url=gallery_url,
            )
            success_count += 1
        except Exception as e:
            logging.error(f"Failed to visualize {dataset_path}: {e}")

    logging.info(f"Successfully visualized {success_count}/{len(to_process)} datasets.")


if __name__ == "__main__":
    app.run(main)
