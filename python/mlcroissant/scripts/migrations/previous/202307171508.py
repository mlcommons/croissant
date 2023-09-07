"""Migrations for source: https://github.com/mlcommons/croissant/issues/115."""

from typing import Any

from mlcroissant._src.core.issues import Issues
from mlcroissant._src.structure_graph.nodes.source import Source


def _is_in(elements: list[Any], name: str):
    for element in elements:
        if element.get("name") == name:
            return True
    return False


def _migrate_source(
    source: Source,
    record_sets: list[Any],
    file_sets: list[Any],
    file_objects: list[Any],
):
    if isinstance(source, dict):
        existing_transforms = source.get("applyTransform", [])
        if not isinstance(existing_transforms, list):
            existing_transforms = [existing_transforms]
        source["apply_transform"] = existing_transforms
    source = Source.from_jsonld(Issues(), source)
    reference = source.reference
    new_source = {}
    apply_transform = []
    for transform in list(source.apply_transform):
        if transform.format:
            apply_transform.append({"format": transform.format})
        elif transform.separator:
            apply_transform.append({"separator": transform.separator})
        elif transform.regex:
            apply_transform.append({"regex": transform.regex})
        elif transform.replace:
            apply_transform.append({"replace": transform.replace})
        else:
            raise ValueError("Impossible case")
    if apply_transform:
        if len(apply_transform) == 1:
            new_source["applyTransform"] = apply_transform[0]
        else:
            new_source["applyTransform"] = apply_transform
    if len(reference) == 2:
        origin, column = reference[0], reference[1]
    elif len(reference) == 1:
        origin, column = reference[0], None
    else:
        raise ValueError("Impossible case")
    # Check if source is a FileObject, FileSet or RecordSet
    if _is_in(record_sets, origin):
        if column is not None:
            new_source["field"] = f"{origin}/{column}"
    elif _is_in(file_sets, origin) or _is_in(file_objects, origin):
        new_source["distribution"] = origin
        if column == "filename" or column == "fullpath" or column == "content":
            new_source["ml:dataExtraction"] = {"fileProperty": column}
        elif column is not None:
            new_source["ml:dataExtraction"] = {"csvColumn": column}
    else:
        raise ValueError("Impossible case")
    return new_source


def up(json_ld):
    """Up migration that converts `source` to a structured source."""
    record_sets = json_ld.get("recordSet")
    if record_sets is None:
        return json_ld
    distribution = json_ld.get("distribution", [])
    if not isinstance(distribution, list):
        distribution = [distribution]
    file_sets = [el for el in distribution if "sc:FileSet" == el.get("@type", "")]
    file_objects = [el for el in distribution if "sc:FileObject" == el.get("@type", "")]
    for i, record_set in enumerate(record_sets):
        fields = record_set.get("field")
        if fields is None:
            continue
        for j, field in enumerate(fields):
            for source_field in ["source", "references"]:
                source = field.get(source_field)
                if source is not None:
                    new_source = _migrate_source(
                        source, record_sets, file_sets, file_objects
                    )
                    if new_source:
                        json_ld["recordSet"][i]["field"][j][source_field] = new_source
                sub_fields = field.get("subField")
                if sub_fields is None:
                    continue
                for k, sub_field in enumerate(sub_fields):
                    source = sub_field.get(source_field)
                    if source is not None:
                        new_source = _migrate_source(
                            source, record_sets, file_sets, file_objects
                        )
                        if new_source:
                            json_ld["recordSet"][i]["field"][j]["subField"][k][
                                source_field
                            ] = new_source
    return json_ld
