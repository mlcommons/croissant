"""Migration: Remove former RAI fields."""


def up(json_ld):
    """Up migration that removes former RAI fields."""
    if "@context" in json_ld:
        for field in ["dataCollection", "personalSensitiveInformation", "dataBiases"]:
            if field in json_ld["@context"]:
                del json_ld["@context"][field]
    return json_ld
