"""Migration: `ml:` -> `cr:`."""

import json


def up(json_ld):
    """Up migration for `ml:` -> `cr:`."""
    json_ld = json.dumps(json_ld)
    json_ld = json_ld.replace("ml:", "cr:")
    json_ld = json.loads(json_ld)
    json_ld["@context"]["cr"] = "http://mlcommons.org/croissant/"
    if "ml" in json_ld["@context"]:
        del json_ld["@context"]["ml"]
    return json_ld
