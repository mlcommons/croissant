"""Migration: http://mlcommons.org/schema/ -> http://mlcommons.org/schema/."""


def up(json_ld):
    """Up migration for http://mlcommons.org/schema/ -> http://mlcommons.org/schema/."""
    json_ld["@context"]["ml"] = "http://mlcommons.org/croissant/"
    return json_ld
