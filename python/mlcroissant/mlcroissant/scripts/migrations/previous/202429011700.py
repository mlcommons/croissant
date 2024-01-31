"""Migration: Remove `distribution` from DataSource, and use `fileObject`/`fileSet`."""


def _migrate_field(json_ld, distribution):
    for field in ["source", "references"]:
        if field in json_ld:
            source = json_ld[field]
            if "distribution" in source:
                resource_name = source["distribution"]
                for resource in distribution:
                    if resource["name"] == resource_name:
                        if resource["@type"] == "sc:FileObject":
                            source["fileObject"] = resource_name
                        elif resource["@type"] == "sc:FileSet":
                            source["fileSet"] = resource_name
                        else:
                            raise ValueError(f"invalid source: {source}")
                del source["distribution"]
                json_ld[field] = source
    return json_ld


def up(json_ld):
    """Up migration that migrates `distribution`->`fileObject`/`fileSet`."""
    json_copy = json_ld.copy()
    distribution = json_copy.get("distribution", [])
    for i, record_set in enumerate(json_copy.get("recordSet", [])):
        fields = record_set.get("field", [])
        if isinstance(fields, dict):
            fields = [fields]
        assert isinstance(fields, list), "RecordSet.field is not a list"
        for j, field in enumerate(fields.copy()):
            field = _migrate_field(field, distribution)
            sub_fields = field.get("subField", [])
            if isinstance(sub_fields, dict):
                sub_fields = [sub_fields]
            for k, sub_field in enumerate(sub_fields.copy()):
                sub_field = _migrate_field(sub_field, distribution)
                field["subField"][k] = sub_field
            record_set["field"][j] = field
        json_ld["recordSet"][i] = record_set
    json_ld["@context"]["fileObject"] = "ml:fileObject"
    json_ld["@context"]["fileSet"] = "ml:fileSet"
    return json_ld
