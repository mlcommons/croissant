"""Visualizes a Croissant dataset."""

import html
import json
import sys
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


def _clean_description(desc: str) -> str:
    """Clean up descriptions by removing tabs and collapsing excessive newlines."""
    if not desc:
        return ""
    # Replace tabs with spaces
    desc = desc.replace("\t", " ")
    # Collapse multiple newlines (more than 2) into 2 newlines
    import re
    desc = re.sub(r"\n{3,}", "\n\n", desc)
    # Strip whitespace from lines that only contain whitespace
    lines = [line if line.strip() else "" for line in desc.split("\n")]
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


def main(argv):
    """Main function launched by the script."""
    del argv
    if not FLAGS.jsonld or not FLAGS.output:
        logging.fatal("Both --jsonld and --output are required when running this script directly.")
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
        "name", "description", "url", "version",
        "distribution", "record_sets",
        "ctx", "folder", "uuid", "rdf", "issues",
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

        metadata_fields.append({
            "name": name.replace("_", " ").title(),
            "raw_name": name,
            "value": value_str,
            "description": field.description or "",
            "jsonld": jsonld_snippet,
        })

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

    # Extract resources and build Mermaid graph
    resources = []
    mermaid_nodes = []
    mermaid_edges = []

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
                        fmt in ["text/csv", "text/plain"]
                        for fmt in encoding_formats
                    ):
                        try:
                            with file_path.open("r") as f:
                                preview = "".join(
                                    [f.readline() for _ in range(5)]
                                )
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
        res_jsonld = _find_jsonld_entry(
            raw_jsonld.get("distribution", []), res_name
        )

        res_data = {
            "name": res_name,
            "type": res_type,
            "type_label": type_label,
            "type_icon": type_icon,
            "description": res.description or "",
            "preview": preview,
            "jsonld": res_jsonld,
        }
        resources.append(res_data)

        # Mermaid node - sanitize name for valid mermaid IDs
        safe_name = res_name.replace("-", "_").replace(" ", "_").replace(".", "_")
        mermaid_nodes.append(
            f'    {safe_name}["{res_name}<br/><small>{type_label}</small>"]'
        )

        # Mermaid edge for contained_in
        if hasattr(res, "contained_in") and res.contained_in:
            for parent in res.contained_in:
                if isinstance(parent, str):
                    safe_parent = parent.replace("-", "_").replace(" ", "_").replace(".", "_")
                    mermaid_edges.append(f"    {safe_parent} --> {safe_name}")
                elif hasattr(parent, "uuid"):
                    safe_parent = (
                        parent.uuid.replace("-", "_").replace(" ", "_").replace(".", "_")
                    )
                    mermaid_edges.append(f"    {safe_parent} --> {safe_name}")

    mermaid_graph = ""
    if mermaid_nodes:
        mermaid_graph = "graph TD\n"
        mermaid_graph += "\n".join(mermaid_nodes) + "\n"
        if mermaid_edges:
            mermaid_graph += "\n".join(mermaid_edges)

    # Extract record sets
    record_sets = []
    for rs in metadata.record_sets:
        # Find the JSON-LD snippet for this record set
        rs_name = rs.name or rs.uuid or "Unnamed"
        rs_jsonld = _find_jsonld_entry(
            raw_jsonld.get("recordSet", []), rs_name
        )

        rs_data = {
            "name": rs_name,
            "description": rs.description or "",
            "fields": [],
            "jsonld": rs_jsonld,
        }
        for field in rs.fields:
            data_type_raw = str(field.data_type) if field.data_type else ""
            # Clean up ugly Python class strings
            data_type_display = data_type_raw
            if data_type_raw.startswith("<class '"):
                data_type_display = data_type_raw.replace("<class '", "").replace("'>", "")
            # Shorten schema.org URLs
            if "schema.org/" in data_type_display:
                data_type_display = data_type_display.split("/")[-1]

            field_data = {
                "name": field.name.split("/")[-1] if "/" in field.name else field.name,
                "full_name": field.name,
                "description": field.description or "",
                "data_type": data_type_display,
            }
            rs_data["fields"].append(field_data)
        record_sets.append(rs_data)

    data = {
        "name": metadata.name,
        "description": _clean_description(metadata.description),
        "url": metadata.url,
        "version": _format_value(metadata.version),
        "metadata_fields": metadata_fields,
        "resources": resources,
        "mermaid_graph": mermaid_graph,
        "record_sets": record_sets,
        "full_jsonld": json.dumps(raw_jsonld, indent=2, ensure_ascii=False),
        "jsonld_filename": jsonld_path.name,
    }

    template = env.get_template("visualizer.html")
    output.write_text(template.render(data))
    print(f"Wrote visualization to {output}")


if __name__ == "__main__":
    app.run(main)
