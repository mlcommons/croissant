"""Module to manipulate UUID."""

import dataclasses
from typing import Any
import uuid

from mlcroissant._src.core.context import Context
from mlcroissant._src.core.types import Json


@dataclasses.dataclass
class Uuid:
    """Unique identifiers used in Croissant."""

    ctx: Context
    uuid: None | str

    def __post_init__(self):
        """Cleanup uuid."""
        self.uuid = self.to_jsonld()

    @classmethod
    def from_jsonld(cls, ctx: Context, jsonld: Json | None) -> "Uuid":
        """Retrieves uuid from a JSON-LD fragment. If no uuid, it will generate one."""
        if isinstance(jsonld, dict):
            uuid = jsonld.get("@id")
            if uuid is None:
                uuid = generate_uuid()
            return cls(uuid=uuid, ctx=ctx)
        elif isinstance(jsonld, str):
            return cls(uuid=jsonld, ctx=ctx)
        return cls(uuid=generate_uuid(), ctx=ctx)

    def to_jsonld(self) -> str | None:
        """Removes the base IRI from an expanded @id."""
        if self.uuid is None:
            return None
        split = self.uuid.split(self.ctx.base_iri)
        if len(split) == 1:
            return split[0]
        return self.ctx.base_iri.join(split[1:])

    def formatted_uuid_to_json(self) -> str | None | dict[str, Any]:
        """Return a formatted node's uuid depending on the Croissant version."""
        if self.ctx.is_v0():
            return self.uuid
        else:
            return {"@id": self.uuid}


def generate_uuid() -> str:
    """Generates a UUID of version 4 because it's random and simple."""
    return str(uuid.uuid4())
