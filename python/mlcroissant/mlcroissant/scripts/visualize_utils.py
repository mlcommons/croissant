"""Shared utility functions for the Croissant dataset visualizer.

These helpers handle data previews (file listings for FileSets, sample
rows for RecordSets) and are imported by ``visualize.py``.
"""

import fnmatch
import json
import pathlib
import re
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


def _sanitize_name(name: str) -> str:
    """Convert a record set name to a filesystem-safe stem."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _find_jsonl_for_recordset(
    rs_name: str, output_dir: pathlib.Path
) -> pathlib.Path | None:
    """Find an existing JSONL file for a record set in the output directory.

    Tries the sanitized full name, then the last path segment, then the first
    word, so that hand-named files like 'bands.jsonl' for 'Spectral Bands' still
    match.
    """
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
    rs_name: str,
    folder: epath.Path | None,
) -> tuple[list[str], list[list[str]]]:
    """Return (columns, rows) for a recordset preview.

    Reads from an existing output/<name>.jsonl when available.  If the dataset
    is fully local and no JSONL exists, generates it via the mlcroissant API
    and writes the file so future runs are instant.

    Returns ([], []) when no preview is available.
    """
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
