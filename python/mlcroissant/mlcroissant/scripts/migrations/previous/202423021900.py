"""Migration: add sdLicense."""


def up(json_ld):
    """Up migration to add sdLicense to all included datasets."""
    json_ld["sdLicense"] = "apache-2.0"
    return json_ld
