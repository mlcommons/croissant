"""FileObject module."""

from __future__ import annotations

import dataclasses
from typing import Any, Callable, Literal

from rdflib import term
from rdflib.namespace import SDO

from mlcroissant._src.core import constants
from mlcroissant._src.core.constants import ML_COMMONS
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.data_types import check_expected_type
from mlcroissant._src.core.json_ld import box_singleton_list
from mlcroissant._src.core.json_ld import remove_empty_values
from mlcroissant._src.core.json_ld import unbox_singleton_list
from mlcroissant._src.core.types import Json
from mlcroissant._src.core.uuid import formatted_uuid_to_json
from mlcroissant._src.core.uuid import uuid_from_jsonld
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.source import Source


class JsonldField(dataclasses.Field):
    """Overloads dataclasses.Field with JSON-LD-specific attributes."""

    def __init__(
        self,
        *args,
        cardinality: Literal["ONE", "MANY"],
        description: str,
        from_jsonld: Callable[[Context, Json], Any] | None,
        input_types: list[Any],
        to_jsonld: Callable[[Context, Json], Any] | None,
        required: bool,
        url: term.URIRef | Callable[[Context], term.URIRef] | None,
    ):
        """Sets all args and kwargs."""
        super().__init__(*args)
        self.cardinality = cardinality
        self.description = description
        self.from_jsonld = from_jsonld
        self.input_types = input_types
        self.to_jsonld = to_jsonld
        self.required = required
        self.url = url

    def call_from_jsonld(self, ctx: Context, value: Any):
        """Calls `from_jsonld` in the field."""
        if value and self.from_jsonld:
            return self.from_jsonld(ctx, value)
        else:
            return value

    def call_to_jsonld(self, ctx: Context, value: Any):
        """Calls `to_jsonld` in the field."""
        if value and self.from_jsonld:
            return self.to_jsonld(ctx, value)
        else:
            return value

    def call_url(self, ctx: Context) -> term.URIRef:
        """Calls `jsonld` in the field."""
        url = self.url
        if url is None:
            return None
        elif isinstance(url, term.URIRef):
            return url
        else:
            return url(ctx)


OriginalField = dataclasses.Field
dataclasses.Field = JsonldField


def jsonld_field(
    default=dataclasses.MISSING,
    default_factory=dataclasses.MISSING,
    init=True,
    repr=True,
    hash=None,
    compare=True,
    metadata=None,
    kw_only=dataclasses.MISSING,
    cardinality="ONE",
    description="",
    from_jsonld=None,
    input_types=None,
    to_jsonld=None,
    required=False,
    url=None,
):
    """Overloads dataclasses.field with specific attributes."""
    if (
        default is not dataclasses.MISSING
        and default_factory is not dataclasses.MISSING
    ):
        raise ValueError("cannot specify both default and default_factory")
    if not input_types or not isinstance(input_types, list):
        raise ValueError(f"input type should be a non-empty list. Got: {input_types}")
    return JsonldField(
        default,
        default_factory,
        init,
        repr,
        hash,
        compare,
        metadata,
        kw_only,
        cardinality=cardinality,
        description=description,
        from_jsonld=from_jsonld,
        input_types=input_types,
        to_jsonld=to_jsonld,
        required=required,
        url=url,
    )


def jsonld_fields(cls_or_instance) -> list[JsonldField]:
    """Filters the JSON-LD fields."""
    return [
        field
        for field in dataclasses.fields(cls_or_instance)
        if isinstance(field, JsonldField)
    ]


@dataclasses.dataclass(eq=False, repr=False)
class FileObject(Node):
    """Nodes to describe a dataset FileObject (distribution)."""

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
        check_expected_type(ctx, jsonld, cls._JSONLD_TYPE(ctx))
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


dataclasses.Field = OriginalField
