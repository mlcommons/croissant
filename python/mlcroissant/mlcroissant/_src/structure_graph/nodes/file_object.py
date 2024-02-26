"""FileObject module."""

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
from mlcroissant._src.structure_graph.nodes.source import Source


@dataclasses.dataclass(eq=False, repr=False)
class FileObject(Node):
    """Nodes to describe a dataset FileObject (distribution)."""

    content_url: str | None = None
    content_size: str | None = None
    contained_in: list[str | dict[str, str | None]] | None = None
    description: str | None = None
    encoding_format: str | None = None
    md5: str | None = None
    name: str = ""
    id: str = ""  # JSON-LD @id
    same_as: list[str] | None = None
    sha256: str | None = None
    source: Source | None = None

    def __post_init__(self):
        """Checks arguments of the node."""
        self.validate_name()
        self.assert_has_mandatory_properties("encoding_format", "name", "id")
        if not self.contained_in:
            self.assert_has_mandatory_properties("content_url")
            if self.ctx and not self.ctx.is_live_dataset:
                self.assert_has_exclusive_properties(["md5", "sha256"])

    def to_json(self) -> Json:
        """Converts the `FileObject` to JSON."""
        contained_in = self.contained_in
        if not self.ctx.is_v0():
            if isinstance(contained_in, list):
                contained_in = [
                    {"@id": uuid_to_jsonld(source)} for source in contained_in  # type: ignore[arg-type]
                ]
            elif isinstance(contained_in, str):
                contained_in = {"@id": uuid_to_jsonld(contained_in)}
        contained_in = unbox_singleton_list(contained_in)

        json_output = remove_empty_values({
            "@type": "sc:FileObject" if self.ctx.is_v0() else "cr:FileObject",
            "@id": None if self.ctx.is_v0() else uuid_to_jsonld(self.uuid),
            "name": self.name,
            "description": self.description,
            "contentSize": self.content_size,
            "contentUrl": self.content_url,
            "containedIn": contained_in,
            "encodingFormat": self.encoding_format,
            "md5": self.md5,
            "sameAs": unbox_singleton_list(self.same_as),
            "sha256": self.sha256,
            "source": self.source.to_json(ctx=self.ctx) if self.source else None,
        })
        return json_output

    @classmethod
    def from_jsonld(
        cls,
        ctx: Context,
        file_object: Json,
    ) -> FileObject:
        """Creates a `FileObject` from JSON-LD."""
        check_expected_type(
            ctx.issues, file_object, constants.SCHEMA_ORG_FILE_OBJECT(ctx)
        )
        content_url = file_object.get(constants.SCHEMA_ORG_CONTENT_URL)
        name = file_object.get(constants.SCHEMA_ORG_NAME, "")

        contained_in = box_singleton_list(
            file_object.get(constants.SCHEMA_ORG_CONTAINED_IN)
        )
        if contained_in is not None and not ctx.is_v0():
            contained_in = [uuid_from_jsonld(source) for source in contained_in]
        content_size = file_object.get(constants.SCHEMA_ORG_CONTENT_SIZE)
        description = file_object.get(constants.SCHEMA_ORG_DESCRIPTION)
        encoding_format = file_object.get(constants.SCHEMA_ORG_ENCODING_FORMAT)
        return cls(
            ctx=ctx,
            content_url=content_url,
            content_size=content_size,
            contained_in=contained_in,
            description=description,
            encoding_format=encoding_format,
            md5=file_object.get(constants.SCHEMA_ORG_MD5(ctx)),
            name=name,
            same_as=box_singleton_list(file_object.get(constants.SCHEMA_ORG_SAME_AS)),
            sha256=file_object.get(constants.SCHEMA_ORG_SHA256),
            source=file_object.get(constants.ML_COMMONS_SOURCE(ctx)),
            id=uuid_from_jsonld(file_object),
        )
