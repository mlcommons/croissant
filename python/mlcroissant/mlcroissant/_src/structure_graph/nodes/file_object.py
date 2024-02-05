"""FileObject module."""

from __future__ import annotations

import dataclasses

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.data_types import check_expected_type
from mlcroissant._src.core.json_ld import remove_empty_values
from mlcroissant._src.core.types import Json
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.source import Source


@dataclasses.dataclass(eq=False, repr=False)
class FileObject(Node):
    """Nodes to describe a dataset FileObject (distribution)."""

    content_url: str | None = None
    content_size: str | None = None
    contained_in: list[str] = dataclasses.field(default_factory=list)
    description: str | None = None
    encoding_format: str | None = None
    md5: str | None = None
    name: str = ""
    sha256: str | None = None
    source: Source | None = None

    def __post_init__(self):
        """Checks arguments of the node."""
        self.validate_name()
        self.assert_has_mandatory_properties("encoding_format", "name")
        if not self.contained_in:
            self.assert_has_mandatory_properties("content_url")
            self.assert_has_exclusive_properties(["md5", "sha256"])

    def to_json(self) -> Json:
        """Converts the `FileObject` to JSON."""
        if isinstance(self.contained_in, list) and len(self.contained_in) == 1:
            contained_in: str | list[str] = self.contained_in[0]
        else:
            contained_in = self.contained_in
        return remove_empty_values({
            "@type": "sc:FileObject" if self.ctx.is_v0() else "cr:FileObject",
            "name": self.name,
            "description": self.description,
            "contentSize": self.content_size,
            "contentUrl": self.content_url,
            "containedIn": contained_in,
            "encodingFormat": self.encoding_format,
            "md5": self.md5,
            "sha256": self.sha256,
            "source": self.source.to_json() if self.source else None,
        })

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
        contained_in = file_object.get(constants.SCHEMA_ORG_CONTAINED_IN, [])
        name = file_object.get(constants.SCHEMA_ORG_NAME, "")
        if contained_in is not None and not isinstance(contained_in, list):
            contained_in = [contained_in]
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
            sha256=file_object.get(constants.SCHEMA_ORG_SHA256),
            source=file_object.get(constants.ML_COMMONS_SOURCE(ctx)),
        )
