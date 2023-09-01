"""Migration: https://github.com/mlcommons/croissant/discussions/151."""


def _migrate_field(json_ld):
    for field in ["source", "references"]:
        if field in json_ld:
            source = json_ld[field]
            for old_name, new_name in [
                ("dataExtraction", "extract"),
                ("applyTransform", "transform"),
            ]:
                if old_name in source:
                    source[new_name] = source[old_name]
                    del source[old_name]
            # Sort keys
            source = {k: v for k, v in sorted(source.items())}
            json_ld[field] = source
    return json_ld


def up(json_ld):
    """Up migration that converts `containedIn` to the new format."""
    json_copy = json_ld.copy()
    for i, record_set in enumerate(json_copy.get("recordSet", [])):
        fields = record_set.get("field", [])
        if isinstance(fields, dict):
            fields = [fields]
        for j, field in enumerate(fields):
            field = _migrate_field(field)
            sub_fields = field.get("subField", [])
            if isinstance(sub_fields, dict):
                sub_fields = [sub_fields]
            for k, sub_field in enumerate(sub_fields):
                sub_field = _migrate_field(sub_field)
                field["subField"][k] = sub_field
            record_set["field"][j] = field
        json_ld["recordSet"][i] = record_set
    json_ld["@context"]["extract"] = "ml:extract"
    json_ld["@context"]["transform"] = "ml:transform"
    if "applyTransform" in json_ld["@context"]:
        del json_ld["@context"]["applyTransform"]
    if "dataExtraction" in json_ld["@context"]:
        del json_ld["@context"]["dataExtraction"]
    return json_ld
