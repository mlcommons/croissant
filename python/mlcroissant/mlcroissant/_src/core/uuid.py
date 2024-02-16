"""Module to manipulate UUID."""

import uuid

from mlcroissant._src.core.types import Json


def generate_uid() -> str:
    """Generates a UUID of version 4 because it's random and simple."""
    return str(uuid.uuid4())


def uuid_from_jsonld(jsonld: Json) -> str:
    """Retrieves uuid from a JSON-LD fragment."""
    uuid = jsonld.get("@id")
    if isinstance(uuid, str):
        return uuid
    return generate_uid()
