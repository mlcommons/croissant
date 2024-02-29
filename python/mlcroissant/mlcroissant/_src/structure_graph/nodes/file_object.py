"""FileObject module."""

from __future__ import annotations

import dataclasses

from rdflib.namespace import SDO

from mlcroissant._src.core import constants
from mlcroissant._src.core.constants import ML_COMMONS
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.data_types import check_expected_type
from mlcroissant._src.core.dataclasses import jsonld_field
from mlcroissant._src.core.dataclasses import jsonld_fields
from mlcroissant._src.core.dataclasses import JsonldField
from mlcroissant._src.core.json_ld import box_singleton_list
from mlcroissant._src.core.json_ld import remove_empty_values
from mlcroissant._src.core.json_ld import unbox_singleton_list
from mlcroissant._src.core.types import Json
from mlcroissant._src.core.uuid import formatted_uuid_to_json
from mlcroissant._src.core.uuid import uuid_from_jsonld
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.source import Source

OriginalField = dataclasses.Field
dataclasses.Field = JsonldField  # type: ignore


@dataclasses.dataclass(eq=False, repr=False)
class FileObject(Node):
    """Nodes to describe a dataset FileObject (distribution)."""

    # pytype: disable=annotation-type-mismatch
    content_url: str | None = jsonld_field(
        default=None,
        description=(
            "Actual bytes of the media object, for example the image file or"
            " video file."
        ),
        input_types=[SDO.URL],
        url=SDO.contentUrl,
    )
    content_size: str | None = jsonld_field(
        default=None,
        description=(
            "File size in (mega/kilo/…)bytes. Defaults to bytes if a unit is"
            " not specified."
        ),
        input_types=[SDO.Text],
        url=SDO.contentSize,
    )
    contained_in: list[str] | None = jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description=(
            "Another FileObject or FileSet that this one is contained in, e.g.,"
            " in the case of a file extracted from an archive. When this"
            " property is present, the contentUrl is evaluated as a relative"
            " path within the container object"
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
        default=None,
        description=(
            "The name of the file.  As much as possible, the name should"
            " reflect the name of the file as downloaded, including the file"
            " extension. e.g. “images.zip”."
        ),
        input_types=[SDO.Text],
        required=True,
        url=SDO.name,
    )
    same_as: list[str] | None = jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description=(
            "URL (or local name) of a FileObject with the same content, but in"
            " a different format."
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
        self.assert_has_mandatory_properties("encoding_format", "name", "id")
        if not self.contained_in:
            self.assert_has_mandatory_properties("content_url")
            if self.ctx and not self.ctx.is_live_dataset:
                self.assert_has_exclusive_properties(["md5", "sha256"])

    @classmethod
    def _JSONLD_TYPE(cls, ctx: Context):
        """Gets the class' JSON-LD @type."""
        return constants.SCHEMA_ORG_FILE_OBJECT(ctx)

    # [Proposal] This method would move to `Node`, as it's now generic.
    def to_json(self) -> Json:
        """Converts the `FileObject` to JSON."""
        cls = self.__class__
        jsonld = {
            "@type": self.ctx.rdf.shorten_value(cls._JSONLD_TYPE(self.ctx)),
            "@id": None if self.ctx.is_v0() else self.id,
        }
        for field in jsonld_fields(self):
            url = field.call_url(self.ctx)
            key = url.split("/")[-1]
            value = getattr(self, field.name)
            value = field.call_to_jsonld(self.ctx, value)
            if field.cardinality == "MANY":
                value = unbox_singleton_list(value)
            jsonld[key] = value
        return remove_empty_values(jsonld)

    # [Proposal] This method would move to `Node`, as it's now generic.
    @classmethod
    def from_jsonld(cls, ctx: Context, jsonld: Json) -> FileObject:
        """Creates a `FileObject` from JSON-LD."""
        check_expected_type(ctx.issues, jsonld, cls._JSONLD_TYPE(ctx))
        kwargs = {}
        for field in jsonld_fields(cls):
            url = field.call_url(ctx)
            value = jsonld.get(url)
            value = field.call_from_jsonld(ctx, value)
            if field.cardinality == "MANY":
                value = box_singleton_list(value)
            if value:
                kwargs[field.name] = value
        # Normalize name to be at least an empty str:
        kwargs["name"] = kwargs.get("name", "")
        return cls(
            ctx=ctx,
            id=uuid_from_jsonld(jsonld),
            **kwargs,
        )


dataclasses.Field = OriginalField  # type: ignore
