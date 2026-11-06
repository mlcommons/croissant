"""Shared utility functions for the Croissant dataset visualizer.

These helpers handle data previews (file listings for FileSets, sample
rows for RecordSets) and are imported by ``visualize.py``.
"""

import copy
import fnmatch
import json
import pathlib
import re
import shutil
import sys
import tarfile
from typing import Any
import zipfile

from absl import logging
from etils import epath

import mlcroissant as mlc

_MAX_PREVIEW_FILES = 10
_MAX_PREVIEW_ROWS = 5
_MAX_PREVIEW_COLS = 10


def _list_archive_entries(file_path: str, encoding_formats: list[str]) -> list[str]:
    """List file entries inside a local archive (tar or zip)."""
    entries = []
    try:
        if any("tar" in fmt for fmt in encoding_formats):
            with tarfile.open(file_path) as t:
                entries = [m.name for m in t.getmembers() if m.isfile()]
        elif any("zip" in fmt for fmt in encoding_formats):
            with zipfile.ZipFile(file_path) as z:
                entries = [n for n in z.namelist() if not n.endswith("/")]
    except Exception as e:
        logging.warning(f"Failed to list archive entries for {file_path}: {e}")
    return entries


def _resolve_fileset_files(res, distribution, folder) -> tuple[list[str], int]:
    """Resolve the actual files in a FileSet by inspecting its container archives.

    Returns a tuple of (file_list, total_count) where file_list is capped at
    _MAX_PREVIEW_FILES entries and total_count is the full number of matching files.
    """
    if not hasattr(res, "includes") or not res.includes:
        return [], 0
    if not hasattr(res, "contained_in") or not res.contained_in:
        return [], 0

    # Build lookup from name/uuid -> resource
    res_by_id = {}
    for r in distribution:
        if r.name:
            res_by_id[r.name] = r
        if r.uuid:
            res_by_id[r.uuid] = r

    all_matched = []
    for parent_ref in res.contained_in:
        if not isinstance(parent_ref, str):
            continue  # Skip Source objects (remote/transform-based refs)
        parent = res_by_id.get(parent_ref)
        if not parent or not hasattr(parent, "content_url") or not parent.content_url:
            continue
        content_url = str(parent.content_url)
        if content_url.startswith("http") or content_url.startswith("s3://"):
            continue  # Remote file, can't inspect locally
        if not folder:
            continue
        file_path = folder / content_url
        if not file_path.exists():
            continue

        enc = getattr(parent, "encoding_formats", []) or []
        if isinstance(enc, str):
            enc = [enc]
        archive_entries = _list_archive_entries(str(file_path), enc)
        if not archive_entries:
            continue

        for pattern in res.includes:
            for entry in archive_entries:
                basename = entry.split("/")[-1]
                if fnmatch.fnmatch(basename, pattern) or fnmatch.fnmatch(
                    entry, pattern
                ):
                    all_matched.append(entry)

    total = len(all_matched)
    return all_matched[:_MAX_PREVIEW_FILES], total


def _is_local_dataset(distribution) -> bool:
    """Returns True if all FileObjects reference local files (no http/s3/git URLs)."""
    for res in distribution:
        content_url = getattr(res, "content_url", None)
        if content_url:
            url_str = str(content_url)
            if (
                url_str.startswith("http")
                or url_str.startswith("s3://")
                or url_str.startswith("git+")
            ):
                return False
    return True


def _sanitize_name(name: Any) -> str:
    """Convert a record set name to a filesystem-safe stem."""
    if isinstance(name, dict):
        name = name.get("en") or (next(iter(name.values())) if name else "")
    name = str(name)
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _find_jsonl_for_recordset(
    rs_name: Any, output_dir: pathlib.Path
) -> pathlib.Path | None:
    """Find an existing JSONL file for a record set in the output directory.

    Tries the sanitized full name, then the last path segment, then the first
    word, so that hand-named files like 'bands.jsonl' for 'Spectral Bands' still
    match.
    """
    if isinstance(rs_name, dict):
        rs_name = rs_name.get("en") or (next(iter(rs_name.values())) if rs_name else "")
    rs_name = str(rs_name)
    if not output_dir.exists():
        return None
    candidates = []
    full = _sanitize_name(rs_name)
    if full:
        candidates.append(full)
    last = _sanitize_name(rs_name.split("/")[-1].strip())
    if last and last not in candidates:
        candidates.append(last)
    first = _sanitize_name(rs_name.split()[0]) if rs_name.split() else ""
    if first and first not in candidates:
        candidates.append(first)
    for stem in candidates:
        p = output_dir / f"{stem}.jsonl"
        if p.exists():
            return p
    return None


def _serialize_value(v: Any) -> Any:
    """Convert a record value to a JSON-serializable form."""
    if isinstance(v, bytes):
        try:
            return v.decode("utf-8", errors="replace")
        except Exception:
            return repr(v)
    if isinstance(v, dict):
        return {str(k): _serialize_value(vv) for k, vv in v.items()}
    if isinstance(v, (list, tuple)):
        return [_serialize_value(i) for i in v]
    try:
        json.dumps(v)  # test serializability
        return v
    except (TypeError, ValueError):
        return str(v)


def _get_or_generate_recordset_preview(
    dataset: mlc.Dataset,
    rs_name: Any,
    folder: epath.Path | None,
) -> tuple[list[str], list[list[str]]]:
    """Return (columns, rows) for a recordset preview.

    Reads from an existing output/<name>.jsonl when available.  If the dataset
    is fully local and no JSONL exists, generates it via the mlcroissant API
    and writes the file so future runs are instant.

    Returns ([], []) when no preview is available.
    """
    if isinstance(rs_name, dict):
        rs_name = rs_name.get("en") or (next(iter(rs_name.values())) if rs_name else "")
    rs_name = str(rs_name)

    if not folder:
        return [], []

    output_dir = pathlib.Path(str(folder)) / "output"
    existing = _find_jsonl_for_recordset(rs_name, output_dir)

    if existing:
        # Read the first _MAX_PREVIEW_ROWS lines from the existing file
        rows_raw = []
        try:
            with existing.open("r", encoding="utf-8") as f:
                for _ in range(_MAX_PREVIEW_ROWS):
                    line = f.readline()
                    if not line:
                        break
                    rows_raw.append(json.loads(line))
        except Exception as e:
            logging.warning(f"Failed to read {existing}: {e}")
            return [], []
    else:
        # Only generate if the dataset is fully local
        if not _is_local_dataset(dataset.metadata.distribution):
            return [], []
        rows_raw = []
        jsonl_path = output_dir / f"{_sanitize_name(rs_name)}.jsonl"
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            with jsonl_path.open("w", encoding="utf-8") as fout:
                for row in dataset.records(record_set=rs_name):
                    serialized = {str(k): _serialize_value(v) for k, v in row.items()}
                    fout.write(json.dumps(serialized, ensure_ascii=False) + "\n")
                    if len(rows_raw) < _MAX_PREVIEW_ROWS:
                        rows_raw.append(serialized)
            logging.info(f"Wrote recordset preview to {jsonl_path}")
        except Exception as e:
            logging.warning(f"Failed to generate records for {rs_name!r}: {e}")
            # Clean up partial file
            if jsonl_path.exists():
                jsonl_path.unlink()
            return [], []

    if not rows_raw:
        return [], []

    # Flatten nested dicts one level, cap columns
    def _flatten(d: dict, prefix: str = "") -> dict:
        out = {}
        for k, v in d.items():
            key = f"{prefix}{k}" if prefix else k
            if isinstance(v, dict):
                out.update(_flatten(v, key + "/"))
            else:
                out[key] = v
        return out

    flat_rows = [_flatten(r) for r in rows_raw]
    # Collect columns in stable order, capped
    all_cols: list[str] = []
    for r in flat_rows:
        for c in r:
            if c not in all_cols:
                all_cols.append(c)
    cols = all_cols[:_MAX_PREVIEW_COLS]

    # Strip rs_name/ prefix from column headers for display
    def _short_col(c: str) -> str:
        prefix = rs_name.lower().split("/")[-1].strip() + "/"
        cl = c.lower()
        if cl.startswith(prefix):
            return c[len(prefix) :]
        # Also strip if column is "recordset/field" style
        if "/" in c:
            return c.split("/", 1)[-1]
        return c

    display_cols = [_short_col(c) for c in cols]
    table_rows = []
    for r in flat_rows:
        table_rows.append([str(r.get(c, "")) for c in cols])
    return display_cols, table_rows


# Directory containing static assets (visualizer.js, visualizer.css)
_STATIC_DIR = pathlib.Path(__file__).parent / "static"
_TEMPLATES_DIR = pathlib.Path(__file__).parent / "templates"


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
        enc_fmts = dist_entry.get("encodingFormat", [])
        if isinstance(enc_fmts, str):
            enc_fmts = [enc_fmts]

        # Case A: FileObject is a zip archive
        if any("zip" in fmt for fmt in enc_fmts) or (
            isinstance(content_url, str) and content_url.endswith(".zip")
        ):
            if content_url and not str(content_url).startswith("http"):
                file_path = folder / content_url
                if file_path.exists():
                    archive_entries = _list_archive_entries(str(file_path), enc_fmts)
                    if archive_entries:
                        entry["cr:examples"] = {
                            "file_list": archive_entries[:_MAX_PREVIEW_FILES],
                            "file_count": len(archive_entries),
                        }

        # Case A (cont.): FileObject is a tar archive
        elif any("tar" in fmt for fmt in enc_fmts) or any(
            isinstance(content_url, str) and content_url.endswith(ext)
            for ext in [".tar", ".tar.gz", ".tgz"]
        ):
            if content_url and not str(content_url).startswith("http"):
                file_path = folder / content_url
                if file_path.exists():
                    archive_entries = _list_archive_entries(str(file_path), enc_fmts)
                    if archive_entries:
                        entry["cr:examples"] = {
                            "file_list": archive_entries[:_MAX_PREVIEW_FILES],
                            "file_count": len(archive_entries),
                        }

        # Case B: FileObject is contained within a zip archive
        contained_in = dist_entry.get("containedIn")
        if contained_in:
            if isinstance(contained_in, list):
                contained_in = contained_in[0] if contained_in else None

            if isinstance(contained_in, str):
                # Find parent resource
                parent = None
                for res in metadata_distribution:
                    if res.name == contained_in or res.uuid == contained_in:
                        parent = res
                        break

                if parent and hasattr(parent, "content_url") and parent.content_url:
                    parent_url = str(parent.content_url)
                    if not parent_url.startswith("http"):
                        parent_path = folder / parent_url
                        if parent_path.exists():
                            parent_enc = getattr(parent, "encoding_formats", []) or []
                            if isinstance(parent_enc, str):
                                parent_enc = [parent_enc]

                            if any(
                                "zip" in fmt for fmt in parent_enc
                            ) or parent_url.endswith(".zip"):
                                try:
                                    with zipfile.ZipFile(str(parent_path)) as z:
                                        if content_url in z.namelist():
                                            with z.open(content_url) as f:
                                                # Read first 5 lines
                                                lines = []
                                                for _ in range(5):
                                                    line = f.readline()
                                                    if not line:
                                                        break
                                                    lines.append(
                                                        line.decode(
                                                            "utf-8", errors="replace"
                                                        )
                                                    )
                                                text_preview = "".join(lines)
                                                entry["cr:examples"] = {
                                                    "text_preview": text_preview
                                                }
                                except Exception as e:
                                    logging.warning(
                                        f"Failed to read from zip {parent_path}: {e}"
                                    )
                            elif (
                                any("tar" in str(fmt).lower() for fmt in parent_enc)
                                or any(fmt == "application/x-tar" for fmt in parent_enc)
                                or any(
                                    parent_url.endswith(ext)
                                    for ext in [".tar", ".tar.gz", ".tgz"]
                                )
                            ):
                                try:
                                    with tarfile.open(str(parent_path)) as t:
                                        try:
                                            member = t.getmember(content_url)
                                            f_obj = t.extractfile(member)
                                            if f_obj is not None:
                                                # Read first 5 lines
                                                lines = []
                                                for _ in range(5):
                                                    line = f_obj.readline()
                                                    if not line:
                                                        break
                                                    lines.append(
                                                        line.decode(
                                                            "utf-8", errors="replace"
                                                        )
                                                    )
                                                text_preview = "".join(lines)
                                                entry["cr:examples"] = {
                                                    "text_preview": text_preview
                                                }
                                        except KeyError:
                                            logging.warning(
                                                f"File {content_url} not found in tar"
                                                f" {parent_path}"
                                            )
                                except Exception as e:
                                    logging.warning(
                                        f"Failed to read from tar {parent_path}: {e}"
                                    )

        # Original Case: Direct local file
        elif content_url and not str(content_url).startswith("http"):
            file_path = folder / content_url
            if file_path.exists():
                if (
                    enc_fmts
                    and any(
                        fmt in ["text/csv", "text/plain", "application/json"]
                        for fmt in enc_fmts
                    )
                ) or (isinstance(content_url, str) and content_url.endswith(".json")):
                    try:
                        with file_path.open("r") as f:
                            text_preview = "".join([f.readline() for _ in range(5)])
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


def visualize_js(
    jsonld: str,
    output: epath.Path,
    static_path: str = ".",
    gallery_url: str | None = None,
) -> None:
    """Generate a JS-driven visualization HTML page for a Croissant dataset.

    Args:
        jsonld: Path to the Croissant JSON-LD file.
        output: Output HTML file path.
        static_path: Path or URL to the js/css directory.
        gallery_url: Optional relative URL back to the gallery index (e.g.
            ``../../index.html``). When set, the visualizer renders a
            "\u2190 All Datasets" back-link in the sidebar. Only passed by
            ``visualize_all.py``; defaults to None so that single-dataset
            local renders are unaffected.
    """
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
        _augment_distribution(d, metadata.distribution, folder) for d in distributions
    ]
    augmented["distribution"] = augmented_dists

    # Augment record sets with cr:examples
    record_sets = augmented.get("recordSet", [])
    if not isinstance(record_sets, list):
        record_sets = [record_sets]
    augmented_rs = [_augment_record_set(rs, dataset, folder) for rs in record_sets]
    augmented["recordSet"] = augmented_rs

    # Inject the augmented JSON-LD inline into the HTML template.
    # A simple placeholder replacement keeps this Jinja2-free.
    # The inline <script> sets window.__CROISSANT_DATA__ synchronously,
    # so the page works from file:// with no web server required.
    output_dir = pathlib.Path(str(output)).parent
    data_script = (
        "<script>window.__CROISSANT_DATA__ = "
        + json.dumps(augmented, indent=2, ensure_ascii=False)
        + ";</script>"
    )
    # Optional back-link to gallery index (only injected by visualize_all.py).
    gallery_script = (
        f"<script>window.__GALLERY_URL__={json.dumps(gallery_url)};</script>"
        if gallery_url is not None
        else ""
    )
    template_html = (_TEMPLATES_DIR / "visualizer.html").read_text(encoding="utf-8")
    html = template_html.replace("<!-- DATASET_DATA -->", data_script)
    html = html.replace("<!-- GALLERY_URL -->", gallery_script)
    html = html.replace("STATIC_PATH", static_path)
    pathlib.Path(str(output)).write_text(html, encoding="utf-8")
    print(f"Wrote visualization to {output}")

    # Copy static assets next to the output file if using default path
    if static_path == ".":
        for asset in ("visualizer.js", "visualizer.css"):
            src = _STATIC_DIR / asset
            dst = output_dir / asset
            if src.exists():
                shutil.copy(src, dst)
                logging.info(f"Copied {src} -> {dst}")
            else:
                logging.warning(f"Static asset not found: {src}")
