"""FileObject module."""

from __future__ import annotations

import dataclasses

from rdflib.namespace import SDO

from mlcroissant._src.core import constants
from mlcroissant._src.core.constants import ML_COMMONS
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.dataclasses import jsonld_field
from mlcroissant._src.core.dataclasses import JsonldField
from mlcroissant._src.core.uuid import formatted_uuid_to_json
from mlcroissant._src.core.uuid import uuid_from_jsonld
from mlcroissant._src.structure_graph.base_node import NodeV2
from mlcroissant._src.structure_graph.nodes.source import Source

OriginalField = dataclasses.Field
dataclasses.Field = JsonldField  # type: ignore


@dataclasses.dataclass(eq=False, repr=False)
class FileObject(NodeV2):
    """Nodes to describe a dataset FileObject (distribution)."""

    # pytype: disable=annotation-type-mismatch
    content_url: str | None = jsonld_field(
        default=None,
        description=(
            "Actual bytes of the media object, for example the image file or video"
            " file."
        ),
        input_types=[SDO.URL],
        url=SDO.contentUrl,
    )
    content_size: str | None = jsonld_field(
        default=None,
        description=(
            "File size in (mega/kilo/...)bytes. Defaults to bytes if a unit is not"
            " specified."
        ),
        input_types=[SDO.Text],
        url=SDO.contentSize,
    )
    contained_in: list[str] | None = jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description=(
            "Another FileObject or FileSet that this one is contained in, e.g., in the"
            " case of a file extracted from an archive. When this property is present,"
            " the contentUrl is evaluated as a relative path within the container"
            " object"
        ),
        from_jsonld=lambda ctx, contained_in: uuid_from_jsonld(contained_in),
        input_types=[SDO.Text],
        to_jsonld=lambda ctx, contained_in: [
            formatted_uuid_to_json(ctx, uuid) for uuid in contained_in
        ],
        url=SDO.containedIn,
    )
    description: str | None = jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=SDO.description,
    )
    encoding_format: str | None = jsonld_field(
        default=None,
        description="The format of the file, given as a mime type.",
        input_types=[SDO.Text],
        required=True,
        url=SDO.encodingFormat,
    )
    md5: str | None = jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=lambda ctx: ML_COMMONS(ctx).md5,
    )
    name: str = jsonld_field(
        default="",
        description=(
            "The name of the file.  As much as possible, the name should reflect the"
            " name of the file as downloaded, including the file extension. e.g."
            ' "images.zip".'
        ),
        input_types=[SDO.Text],
        required=True,
        url=SDO.name,
    )
    same_as: list[str] | None = jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description=(
            "URL (or local name) of a FileObject with the same content, but in a"
            " different format."
        ),
        input_types=[SDO.URL],
        url=SDO.sameAs,
    )
    sha256: str | None = jsonld_field(
        cardinality="ONE",
        default=None,
        description="Checksum for the file contents.",
        input_types=[SDO.Text],
        url=SDO.sha256,
    )
    source: Source | None = jsonld_field(
        default=None,
        input_types=[Source],
        url=lambda ctx: ML_COMMONS(ctx).source,
    )
    # pytype: enable=annotation-type-mismatch

    def __post_init__(self):
        """Checks arguments of the node."""
        self.validate_name()
        uuid_field = "name" if self.ctx.is_v0() else "id"
        self.assert_has_mandatory_properties("encoding_format", uuid_field)

        if not self.contained_in:
            self.assert_has_mandatory_properties("content_url")
            if self.ctx and not self.ctx.is_live_dataset:
                self.assert_has_exclusive_properties(["md5", "sha256"])

    @classmethod
    def _JSONLD_TYPE(cls, ctx: Context):
        """Gets the class' JSON-LD @type."""
        return constants.SCHEMA_ORG_FILE_OBJECT(ctx)


dataclasses.Field = OriginalField  # type: ignore
