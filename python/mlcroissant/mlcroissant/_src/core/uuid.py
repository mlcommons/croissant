"""Module to manipulate UUID."""

from typing import Any
import uuid

from mlcroissant._src.core.constants import BASE_IRI
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.types import Json


def generate_uuid() -> str:
    """Generates a UUID of version 4 because it's random and simple."""
    return f"_:{str(uuid.uuid4())}"


def uuid_from_jsonld(jsonld: Json | None) -> str:
    """Retrieves uuid from a JSON-LD fragment. If no uuid, it will generate one."""
    if isinstance(jsonld, dict):
        uuid = jsonld.get("@id")
        return uuid_from_jsonld(uuid)
    elif isinstance(jsonld, list):
        return [uuid_from_jsonld(uuid) for uuid in jsonld]
    elif isinstance(jsonld, str):
        return uuid_to_jsonld(jsonld)
    return generate_uuid()


def uuid_to_jsonld(uuid: str | None) -> str | None:
    """Removes the base IRI from an expanded @id."""
    if uuid is None:
        return None
    split = uuid.split(BASE_IRI)
    if len(split) == 1:
        return split[0]
    return BASE_IRI.join(split[1:])


def formatted_uuid_to_json(
    ctx: Context, uuid: None | str | list[str]
) -> str | dict[str, Any] | list[dict[str, Any]] | None:
    """Return a formatted node's uuid depending on the Croissant version."""
    if ctx.is_v0():
        return uuid  # type: ignore  # Force mypy types.
    else:
        if isinstance(uuid, list):
            if len(uuid) == 1:
                return {"@id": uuid[0]}
            else:
                return [{"@id": _uuid} for _uuid in uuid]
        elif isinstance(uuid, str):
            return {"@id": uuid}
        else:
            raise ValueError(f"Unknown uuid type: uuid is of type {type(uuid)}.")
