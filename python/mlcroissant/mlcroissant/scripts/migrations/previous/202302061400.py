"""Migration: citation should be citeAs."""


def up(json_ld):
    """Up migration to set conformsTo to croissant specs 1.0."""
    if "citation" in json_ld:
        json_ld["citeAs"] = json_ld["citation"]
        del json_ld["citation"]
    return json_ld
