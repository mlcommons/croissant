"""Migration: Uniforme names and ids.

In fields and record sets, make the names the same as the ids, as it is mostly done in
the specs.
"""


def up(json_ld):
    """Up function."""
    json_copy = json_ld.copy()
    for _, record_set in enumerate(json_copy.get("recordSet", [])):
        if record_set["@id"] != record_set["name"]:
            record_set["name"] = record_set["@id"]
        fields = record_set.get("field", [])
        for _, field in enumerate(fields):
            if field["@id"] != field["name"]:
                field["name"] = field["@id"]
    return json_ld
