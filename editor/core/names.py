"""Module to handle naming of RecordSets and distribution."""


def find_unique_name(names: set[str], name: str):
    """Find a unique UID."""
    while name in names:
        name = f"{name}_0"
    return name
