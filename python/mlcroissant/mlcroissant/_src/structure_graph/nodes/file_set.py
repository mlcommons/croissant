"""FileSet module."""

from __future__ import annotations

import dataclasses

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.data_types import check_expected_type
from mlcroissant._src.core.json_ld import box_singleton_list
from mlcroissant._src.core.json_ld import remove_empty_values
from mlcroissant._src.core.json_ld import unbox_singleton_list
from mlcroissant._src.core.types import Json
from mlcroissant._src.core.uuid import uuid_from_jsonld
from mlcroissant._src.core.uuid import uuid_to_jsonld
from mlcroissant._src.structure_graph.base_node import Node


@dataclasses.dataclass(eq=False, repr=False)
class FileSet(Node):
    """Nodes to describe a dataset FileSet (distribution)."""

    contained_in: list[str] | None = None
    description: str | None = None
    encoding_format: str | None = None
    excludes: list[str] | None = None
    includes: list[str] | None = None
    name: str = ""
    id: str = ""  # JSON-LD @id

    def __post_init__(self):
        """Checks arguments of the node."""
        self.validate_name()
        self.assert_has_mandatory_properties(
            "includes", "encoding_format", "name", "id"
        )

    def to_json(self) -> Json:
        """Converts the `FileSet` to JSON."""
        contained_in = self.contained_in
        if not self.ctx.is_v0():
            if isinstance(contained_in, list):
                contained_in = [{"@id": uuid_to_jsonld(source)} for source in contained_in]  # type: ignore
            elif isinstance(contained_in, str):
                contained_in = {"@id": uuid_to_jsonld(contained_in)}
        contained_in = unbox_singleton_list(contained_in)

        json_output = remove_empty_values({
            "@type": "sc:FileSet" if self.ctx.is_v0() else "cr:FileSet",
            "@id": None if self.ctx.is_v0() else uuid_to_jsonld(self.uuid),
            "name": self.name,
            "description": self.description,
            "containedIn": contained_in,
            "encodingFormat": self.encoding_format,
            "excludes": unbox_singleton_list(self.excludes),
            "includes": unbox_singleton_list(self.includes),
        })
        return json_output

    @classmethod
    def from_jsonld(
        cls,
        ctx: Context,
        file_set: Json,
    ) -> FileSet:
        """Creates a `FileSet` from JSON-LD."""
        check_expected_type(ctx.issues, file_set, constants.SCHEMA_ORG_FILE_SET(ctx))

        contained_in = box_singleton_list(
            file_set.get(constants.SCHEMA_ORG_CONTAINED_IN)
        )
        if contained_in is not None and not ctx.is_v0():
            contained_in = [uuid_from_jsonld(source) for source in contained_in]

        return cls(
            ctx=ctx,
            contained_in=contained_in,
            description=file_set.get(constants.SCHEMA_ORG_DESCRIPTION),
            encoding_format=file_set.get(constants.SCHEMA_ORG_ENCODING_FORMAT),
            excludes=box_singleton_list(
                file_set.get(constants.ML_COMMONS_EXCLUDES(ctx))
            ),
            includes=box_singleton_list(
                file_set.get(constants.ML_COMMONS_INCLUDES(ctx))
            ),
            name=file_set.get(constants.SCHEMA_ORG_NAME, ""),
            id=uuid_from_jsonld(file_set),
        )
