"""Module to handle naming of RecordSets and distribution."""

import re

NAME_PATTERN_REGEX = "[^a-zA-Z0-9\\-_\\.]"


def find_unique_name(names: set[str], name: str):
    """Find a unique UID."""
    name = re.sub(NAME_PATTERN_REGEX, "_", name)
    while name in names:
        name = f"{name}_0"
    return name
