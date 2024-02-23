"""Migrate to use @id for referencing.

For context: https://github.com/mlcommons/croissant/discussions/506.
"""

from mlcroissant._src.core.rdf import make_context


def migrate_distribution(distribution):
    """Add ids to distributions."""
    for d in distribution:
        d["@id"] = d["name"]
        if "containedIn" in d:
            d_id = d["containedIn"]
            if isinstance(d_id, list):
                output_list = [{"@id": d} for d in d_id]
                d["containedIn"] = output_list
            else:
                d["containedIn"] = {"@id": d_id}


def get_distr_uuid(element, distribution):
    """Get the id of a distribution."""
    for d in distribution:
        if element == d["name"]:
            return d["@id"]
    raise KeyError(f"No {element} in current distribution: {distribution}")


def _migrate_field(json_ld, record_set, distribution):
    """Get the id to the different elements of the jsonld."""
    # Add @id to field.
    field_uuid = record_set["@id"] + "/" + json_ld["name"]
    json_ld["@id"] = field_uuid

    if "source" in json_ld:
        source = json_ld["source"]
        if "fileObject" in source:
            d_uuid = get_distr_uuid(source["fileObject"], distribution)
            json_ld["source"]["fileObject"] = {"@id": d_uuid}
        elif "fileSet" in source:
            d_uuid = get_distr_uuid(source["fileSet"], distribution)
            json_ld["source"]["fileSet"] = {"@id": d_uuid}
        elif "field" in source:
            d_uuid = json_ld["source"]["field"]
            json_ld["source"]["field"] = {"@id": d_uuid}
        else:
            raise ValueError("Source should be a field, file_object or a file_set")

    if "references" in json_ld:
        references = json_ld["references"]
        if "fileObject" in references:
            d_uuid = get_distr_uuid(references["fileObject"], distribution)
            json_ld["references"]["fileObject"] = {"@id": d_uuid}
        elif "fileSet" in references:
            d_uuid = get_distr_uuid(references["fileSet"], distribution)
            json_ld["references"]["fileSet"] = {"@id": d_uuid}
        elif "field" in references:
            d_uuid = json_ld["references"]["field"]
            json_ld["references"]["field"] = {"@id": d_uuid}
        else:
            raise ValueError("Reference should be a field, file_object or a file_set")

    return json_ld


def up(json_ld):
    """Up migration that migrates references to use @id."""
    json_copy = json_ld.copy()
    distribution = json_copy.get("distribution", [])
    json_ld["@context"] = make_context()

    # Add @id to distribution.
    migrate_distribution(distribution)

    for i, record_set in enumerate(json_copy.get("recordSet", [])):
        fields = record_set.get("field", [])
        if isinstance(fields, dict):
            fields = [fields]
        assert isinstance(fields, list), "RecordSet.field is not a list"

    for i, record_set in enumerate(json_copy.get("recordSet", [])):
        # Add @id to recordSet
        record_set["@id"] = record_set["name"]
        fields = record_set.get("field", [])
        if isinstance(fields, dict):
            fields = [fields]
        assert isinstance(fields, list), "RecordSet.field is not a list"
        for j, field in enumerate(fields.copy()):
            field = _migrate_field(field, record_set, distribution)
            sub_fields = field.get("subField", [])
            if isinstance(sub_fields, dict):
                sub_fields = [sub_fields]
            for k, sub_field in enumerate(sub_fields.copy()):
                sub_field = _migrate_field(sub_field, record_set, distribution)
                field["subField"][k] = sub_field
            record_set["field"][j] = field
        json_ld["recordSet"][i] = record_set

    return json_ld
