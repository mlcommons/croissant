"""Migration: add sdLicense."""


def up(json_ld):
    """Up migration to add sdLicense to all included datasets."""
    json_ld["sdLicense"] = "https://www.apache.org/licenses/LICENSE-2.0"
    return json_ld
