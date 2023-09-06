"""Migration: https://github.com/mlcommons/croissant/issues/200."""


def _migrate_field(json_ld):
    for field in ["source", "references"]:
        if field in json_ld:
            source = json_ld[field]
            if "extract" in source:
                extract = source["extract"]
                if "csvColumn" in extract:
                    extract["column"] = extract["csvColumn"]
                    del extract["csvColumn"]
                    source["extract"] = extract
            json_ld[field] = source
    return json_ld


def up(json_ld):
    """Up migration that migrates `csvColumn`->`column`."""
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
    json_ld["@context"]["column"] = "ml:column"
    if "csvColumn" in json_ld["@context"]:
        del json_ld["@context"]["csvColumn"]
    return json_ld
