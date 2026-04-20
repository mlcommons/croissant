"""Visualizes a Croissant dataset."""

import fnmatch
import json
import pathlib
import re
import sys
import tarfile
from typing import Any
import zipfile

from absl import app
from absl import flags
from absl import logging
from etils import epath
import jinja2

import mlcroissant as mlc
from mlcroissant._src.core import dataclasses as mlc_dataclasses

flags.DEFINE_string(
    "jsonld",
    None,
    "The path or URL to the Croissant JSON-LD file.",
)
flags.DEFINE_string(
    "output",
    None,
    "The output HTML file.",
)

FLAGS = flags.FLAGS


def _format_value(value):
    """Format a value for display, stripping list brackets and empty values."""
    if value is None:
        return None
    if isinstance(value, list):
        # Filter out empty strings/None
        items = [str(v) for v in value if v is not None and str(v).strip()]
        if not items:
            return None
        return ", ".join(items)
    s = str(value).strip()
    if not s or s == "[]" or s == "None":
        return None
    return s


def _clean_description(desc: Any) -> str:
    """Clean up descriptions by removing tabs and collapsing excessive newlines."""
    if not desc:
        return ""
    desc_str = str(desc)
    # Replace tabs with spaces
    desc_str = desc_str.replace("\t", " ")
    # Collapse multiple newlines (more than 2) into 2 newlines
    desc_str = re.sub(r"\n{3,}", "\n\n", desc_str)
    # Strip whitespace from lines that only contain whitespace
    lines = [line if line.strip() else "" for line in desc_str.split("\n")]
    return "\n".join(lines)


def _python_name_to_jsonld_key(python_name: str) -> str:
    """Map Python field names to their JSON-LD key equivalents."""
    # Most Croissant JSON-LD keys are camelCase versions of the snake_case Python names
    mapping = {
        "cite_as": "citeAs",
        "conforms_to": "conformsTo",
        "date_created": "dateCreated",
        "date_modified": "dateModified",
        "date_published": "datePublished",
        "in_language": "inLanguage",
        "same_as": "sameAs",
        "is_live_dataset": "isLiveDataset",
        "content_url": "contentUrl",
        "encoding_format": "encodingFormat",
        "record_sets": "recordSet",
    }
    return mapping.get(python_name, python_name)


def _extract_jsonld_value(raw_jsonld: dict, key: str) -> str:
    """Extract a formatted JSON snippet for a top-level JSON-LD key."""
    if key not in raw_jsonld:
        return ""
    snippet = {key: raw_jsonld[key]}
    return json.dumps(snippet, indent=2, ensure_ascii=False)


def _find_jsonld_entry(entries: list, name: str) -> str:
    """Find a JSON-LD entry by @id or name and return formatted JSON."""
    if not isinstance(entries, list):
        return ""
    for entry in entries:
        if isinstance(entry, dict):
            if entry.get("@id") == name or entry.get("name") == name:
                return json.dumps(entry, indent=2, ensure_ascii=False)
    return ""


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


def main(argv):
    """Main function launched by the script."""
    del argv
    if not FLAGS.jsonld or not FLAGS.output:
        logging.fatal(
            "Both --jsonld and --output are required when running this script directly."
        )
        sys.exit(1)
    jsonld = FLAGS.jsonld
    output = epath.Path(FLAGS.output)
    return visualize(jsonld=jsonld, output=output)


def visualize(jsonld: str, output: epath.Path):
    """Visualizes the dataset."""
    logging.info(f"Loading dataset from {jsonld}")
    try:
        dataset = mlc.Dataset(jsonld)
    except Exception as e:
        logging.error(f"Failed to load dataset: {e}")
        sys.exit(1)

    metadata = dataset.metadata

    # Load raw JSON-LD for source snippets
    jsonld_path = epath.Path(jsonld)
    try:
        raw_jsonld = json.loads(jsonld_path.read_text())
    except Exception:
        raw_jsonld = {}

    loader = jinja2.FileSystemLoader(epath.Path(__file__).parent / "templates")
    env = jinja2.Environment(loader=loader, autoescape=jinja2.select_autoescape())

    # Fields to exclude from the metadata table (shown elsewhere or internal)
    excluded_fields = {
        "name",
        "description",
        "url",
        "version",
        "distribution",
        "record_sets",
        "ctx",
        "folder",
        "uuid",
        "rdf",
        "issues",
    }

    # Extract all metadata fields
    metadata_fields = []
    for field in mlc_dataclasses.jsonld_fields(mlc.Metadata):
        name = field.name
        if name in excluded_fields or name.startswith("_"):
            continue
        raw_value = getattr(metadata, name, None)
        value_str = _format_value(raw_value)
        if value_str is None:
            continue
        # Find the corresponding JSON-LD key for this field
        jsonld_key = _python_name_to_jsonld_key(name)
        jsonld_snippet = _extract_jsonld_value(raw_jsonld, jsonld_key)

        metadata_fields.append(
            {
                "name": name.replace("_", " ").title(),
                "raw_name": name,
                "value": value_str,
                "description": field.description or "",
                "jsonld": jsonld_snippet,
            }
        )

    # Sort fields in a sensible way
    preferred_order = [
        "license",
        "cite_as",
        "conforms_to",
        "date_published",
        "date_created",
        "date_modified",
        "keywords",
        "in_language",
        "creators",
        "publisher",
        "same_as",
    ]

    def sort_key(field):
        raw = field["raw_name"]
        if raw in preferred_order:
            return (preferred_order.index(raw), raw)
        return (len(preferred_order), raw)

    metadata_fields.sort(key=sort_key)

    # Extract resources and build SVG dependency graph
    resources = []

    folder = metadata.ctx.folder
    for res in metadata.distribution:
        preview = None
        if hasattr(res, "content_url") and res.content_url:
            content_url = res.content_url
            if not str(content_url).startswith("http") and folder:
                file_path = folder / content_url
                if file_path.exists():
                    encoding_formats = getattr(res, "encoding_formats", [])
                    if isinstance(encoding_formats, str):
                        encoding_formats = [encoding_formats]
                    if encoding_formats and any(
                        fmt in ["text/csv", "text/plain"] for fmt in encoding_formats
                    ):
                        try:
                            with file_path.open("r") as f:
                                preview = "".join([f.readline() for _ in range(5)])
                        except Exception as e:
                            logging.warning(
                                f"Failed to read preview for {res.name}: {e}"
                            )

        # Determine resource type icon
        res_type = res.__class__.__name__
        if res_type == "FileObject":
            type_label = "File"
            type_icon = "📄"
        elif res_type == "FileSet":
            type_label = "File Set"
            type_icon = "📁"
        else:
            type_label = res_type
            type_icon = "📦"

        # Find the JSON-LD snippet for this resource
        res_name = res.name or res.uuid or "Unnamed"
        res_jsonld = _find_jsonld_entry(raw_jsonld.get("distribution", []), res_name)

        # For FileSets, resolve file listings from archives
        file_list: list[str] = []
        file_count = 0
        includes: list[str] = []
        if res_type == "FileSet":
            includes = getattr(res, "includes", []) or []
            file_list, file_count = _resolve_fileset_files(
                res, metadata.distribution, folder
            )
            # If we couldn't resolve files locally, generate a descriptive preview
            if not file_list and includes:
                preview = "Pattern: " + ", ".join(includes)

        # Extract encoding format for display
        enc_fmts = getattr(res, "encoding_formats", []) or []
        if isinstance(enc_fmts, str):
            enc_fmts = [enc_fmts]
        encoding_format = ", ".join(enc_fmts) if enc_fmts else ""

        # Collect contained_in parents (resource name strings)
        contained_in_names: list[str] = []
        if hasattr(res, "contained_in") and res.contained_in:
            for parent in res.contained_in:
                if isinstance(parent, str):
                    contained_in_names.append(parent)
                elif hasattr(parent, "name") and parent.name:
                    contained_in_names.append(str(parent.name))
                elif hasattr(parent, "uuid") and parent.uuid:
                    contained_in_names.append(str(parent.uuid))

        res_data = {
            "name": res_name,
            "type": res_type,
            "type_label": type_label,
            "type_icon": type_icon,
            "description": res.description or "",
            "encoding_format": encoding_format,
            "preview": preview,
            "file_list": file_list,
            "file_count": file_count,
            "jsonld": res_jsonld,
            "contained_in": contained_in_names,
            "uuid": getattr(res, "uuid", res_name),
        }
        resources.append(res_data)

    _run_visualize_pipeline(
        dataset=dataset,
        metadata=metadata,
        resources=resources,
        metadata_fields=metadata_fields,
        raw_jsonld=raw_jsonld,
        env=env,
        output=output,
        jsonld_path=jsonld_path,
        folder=folder,
    )


def _html_escape(s: str) -> str:
    """Minimally escape a string for use in SVG/HTML attributes."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _build_svg_graph(
    resources: list[dict],
    record_sets: list[dict],
) -> str:
    """Build a static SVG dependency graph.

    Resources are placed on the left column; RecordSets on the right.
    Curved edges connect each RecordSet to the resource(s) it reads from.
    Nodes are anchor links to the corresponding page sections.
    """
    if not resources and not record_sets:
        return ""

    # ── Layout constants ────────────────────────────────────────────────
    NODE_W, NODE_H = 180, 52
    COL_GAP = 220  # horizontal gap between left and right columns
    ROW_GAP = 24  # vertical gap between nodes in same column
    PAD_X, PAD_Y = 60, 24  # outer padding (increased PAD_X to allow arcs on left)
    LEFT_X = PAD_X
    RIGHT_X = PAD_X + NODE_W + COL_GAP

    # ── Position each resource node ─────────────────────────────────────
    res_positions: dict[str, tuple[int, int]] = {}  # name or uuid -> (cx, cy)
    for i, res in enumerate(resources):
        cy = PAD_Y + i * (NODE_H + ROW_GAP) + NODE_H // 2
        pos = (LEFT_X + NODE_W // 2, cy)
        res_positions[res["name"]] = pos
        if "uuid" in res and res["uuid"] != res["name"]:
            res_positions[res["uuid"]] = pos

    # ── Position each recordset node ────────────────────────────────────
    rs_positions: dict[str, tuple[int, int]] = {}  # name -> (cx, cy)
    for i, rs in enumerate(record_sets):
        cy = PAD_Y + i * (NODE_H + ROW_GAP) + NODE_H // 2
        rs_positions[rs["name"]] = (RIGHT_X + NODE_W // 2, cy)

    # ── Compute total SVG dimensions ─────────────────────────────────────
    left_h = len(resources) * (NODE_H + ROW_GAP) - ROW_GAP if resources else 0
    right_h = len(record_sets) * (NODE_H + ROW_GAP) - ROW_GAP if record_sets else 0
    total_h = max(left_h, right_h) + 2 * PAD_Y
    total_w = RIGHT_X + NODE_W + PAD_X if record_sets else LEFT_X + NODE_W + PAD_X

    # ── Colour palette ───────────────────────────────────────────────────
    COLORS = {
        "FileObject": {
            "fill": "#fff7ed",
            "stroke": "#f97316",
            "icon_bg": "#fed7aa",
            "icon": "📄",
        },
        "FileSet": {
            "fill": "#eef2ff",
            "stroke": "#6366f1",
            "icon_bg": "#c7d2fe",
            "icon": "📁",
        },
        "RecordSet": {
            "fill": "#f0fdf4",
            "stroke": "#22c55e",
            "icon_bg": "#bbf7d0",
            "icon": "📋",
        },
    }

    # ── SVG parts ────────────────────────────────────────────────────────
    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {total_w} {total_h}" width="{total_w}" height="{total_h}" '
        f'style="max-width:100%;font-family:Inter,sans-serif;">'
    )

    # Arrow-head markers — one for resource→resource, one for resource→recordset
    parts.append(
        "<defs>"
        '<marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">'
        '<path d="M0,0 L0,6 L8,3 z" fill="#94a3b8"/>'
        "</marker>"
        '<marker id="arr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">'
        '<path d="M0,0 L0,6 L8,3 z" fill="#c7d2fe"/>'
        "</marker>"
        "</defs>"
    )

    def _node(cx: int, cy: int, label: str, node_type: str, href: str) -> str:
        c = COLORS.get(node_type, COLORS["RecordSet"])
        x, y = cx - NODE_W // 2, cy - NODE_H // 2
        short = label if len(label) <= 22 else label[:20] + "…"
        esc_label = _html_escape(short)
        esc_full = _html_escape(label)
        return (
            f'<a xlink:href="{href}" href="{href}">'
            f"<title>{esc_full}</title>"
            f'<rect x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}" '
            f'  rx="8" fill="{c["fill"]}" stroke="{c["stroke"]}" stroke-width="1.5"/>'
            # icon pill
            f'<rect x="{x+8}" y="{cy-12}" width="24" height="24" rx="5" fill="{c["icon_bg"]}"/>'
            f'<text x="{x+20}" y="{cy+5}" text-anchor="middle" font-size="13">{c["icon"]}</text>'
            # label
            f'<text x="{x+40}" y="{cy+4}" font-size="12" font-weight="500" '
            f'  fill="#1e293b" dominant-baseline="middle">{esc_label}</text>'
            f"</a>"
        )

    def _edge(x1: int, y1: int, x2: int, y2: int) -> str:
        # Cubic bezier: control points at midpoint x
        mx = (x1 + x2) // 2
        return (
            f'<path d="M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}" '
            f'fill="none" stroke="#94a3b8" stroke-width="1.5" '
            f'marker-end="url(#arr)" opacity="0.7"/>'
        )

    # Column headers
    if resources:
        mid_left = LEFT_X + NODE_W // 2
        parts.append(
            f'<text x="{mid_left}" y="10" text-anchor="middle" '
            f'font-size="10" font-weight="600" fill="#94a3b8" letter-spacing="0.06em">RESOURCES</text>'
        )
    if record_sets:
        mid_right = RIGHT_X + NODE_W // 2
        parts.append(
            f'<text x="{mid_right}" y="10" text-anchor="middle" '
            f'font-size="10" font-weight="600" fill="#94a3b8" letter-spacing="0.06em">RECORD SETS</text>'
        )

    # Draw resource→resource edges (contained_in, e.g. FileObject inside FileSet)
    for res in resources:
        child_cx, child_cy = res_positions[res["name"]]
        for parent_name in res.get("contained_in", []):
            if parent_name in res_positions:
                p_cx, p_cy = res_positions[parent_name]
                # Arc edge on the left side of the resource column
                # From left-middle of parent to left-middle of child
                x_start = p_cx - NODE_W // 2
                y_start = p_cy
                x_end = child_cx - NODE_W // 2
                y_end = child_cy

                # Control points shifted left by 40px
                ctrl_x = x_start - 40

                parts.append(
                    f'<path d="M{x_start},{y_start} '
                    f"C{ctrl_x},{y_start} "
                    f"{ctrl_x},{y_end} "
                    f'{x_end},{y_end}" '
                    f'fill="none" stroke="#c7d2fe" stroke-width="1.5" '
                    f'stroke-dasharray="5,3" marker-end="url(#arr2)" opacity="0.85"/>'
                )

    # Draw RecordSet→resource edges
    for rs in record_sets:
        rs_cx, rs_cy = rs_positions[rs["name"]]
        for src_name in rs.get("source_distributions", []):
            if src_name in res_positions:
                r_cx, r_cy = res_positions[src_name]
                # edge from right-edge of resource node to left-edge of recordset node
                parts.append(
                    _edge(r_cx + NODE_W // 2, r_cy, rs_cx - NODE_W // 2, rs_cy)
                )

    # Draw resource nodes
    for res in resources:
        cx, cy = res_positions[res["name"]]
        href = f"#res-{_html_escape(res['name'])}"
        parts.append(_node(cx, cy, res["name"], res["type"], href))

    # Draw recordset nodes
    for rs in record_sets:
        cx, cy = rs_positions[rs["name"]]
        href = f"#rs-{_html_escape(rs['name'])}"
        parts.append(_node(cx, cy, rs["name"], "RecordSet", href))

    parts.append("</svg>")
    return "".join(parts)


def _run_visualize_pipeline(
    dataset,
    metadata,
    resources: list[dict],
    metadata_fields: list[dict],
    raw_jsonld: dict,
    env,
    output,
    jsonld_path,
    folder,
) -> None:
    """Extracts record sets, builds SVG graph, renders and writes the template."""
    # Extract record sets
    record_sets = []
    for rs in metadata.record_sets:
        # Find the JSON-LD snippet for this record set
        rs_name = str(rs.name or rs.uuid or "Unnamed")
        rs_jsonld = _find_jsonld_entry(raw_jsonld.get("recordSet", []), rs_name)

        # Get or generate a data preview (reads/writes output/<name>.jsonl)
        preview_cols, preview_rows = _get_or_generate_recordset_preview(
            dataset, rs_name, folder
        )

        # Collect source distributions (resources this recordset reads from)
        source_distributions: set[str] = set()
        for rs_field in rs.fields:
            src = getattr(rs_field, "source", None)
            if src:
                for attr in ("distribution", "file_object", "file_set"):
                    val = getattr(src, attr, None)
                    if val:
                        source_distributions.add(str(val))

        rs_data: dict[str, Any] = {
            "name": rs_name,
            "description": rs.description or "",
            "fields": [],
            "preview_cols": preview_cols,
            "preview_rows": preview_rows,
            "source_distributions": sorted(source_distributions),
            "jsonld": rs_jsonld,
        }
        for rs_field in rs.fields:
            data_type_raw = str(rs_field.data_type) if rs_field.data_type else ""
            # Clean up ugly Python class strings
            data_type_display = data_type_raw
            if data_type_raw.startswith("<class '"):
                data_type_display = data_type_raw.replace("<class '", "").replace(
                    "'>", ""
                )
            # Shorten schema.org URLs
            if "schema.org/" in data_type_display:
                data_type_display = data_type_display.split("/")[-1]

            field_name = str(rs_field.name or rs_field.uuid or "Unnamed")
            field_data = {
                "name": field_name.split("/")[-1] if "/" in field_name else field_name,
                "full_name": field_name,
                "description": rs_field.description or "",
                "data_type": data_type_display,
            }
            rs_data["fields"].append(field_data)
        record_sets.append(rs_data)

    svg_graph = _build_svg_graph(resources, record_sets)

    data = {
        "name": metadata.name,
        "description": _clean_description(metadata.description),
        "url": metadata.url,
        "version": _format_value(metadata.version),
        "metadata_fields": metadata_fields,
        "resources": resources,
        "svg_graph": svg_graph,
        "record_sets": record_sets,
        "full_jsonld": json.dumps(raw_jsonld, indent=2, ensure_ascii=False),
        "jsonld_filename": jsonld_path.name,
    }

    template = env.get_template("visualizer.html")
    output.write_text(template.render(data))
    print(f"Wrote visualization to {output}")


if __name__ == "__main__":
    app.run(main)
