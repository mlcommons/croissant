"""Migrate parameters that don't exist in schema.org."""

import json


def up(json_ld):
    """Performs the following sc->cr migration.

    sc:md5->cr:md5, sc:FileSet->cr:FileSet, sc:FileObject->cr:FileObject, sc:key->cr:key
    """
    json_ld = json.dumps(json_ld)
    json_ld = json_ld.replace("sc:FileObject", "cr:FileObject")
    json_ld = json_ld.replace("sc:FileSet", "cr:FileSet")
    json_ld = json.loads(json_ld)
    json_ld["@context"]["key"] = "cr:key"
    json_ld["@context"]["md5"] = "cr:md5"
    return json_ld
