"""FileObject module."""

from __future__ import annotations

import dataclasses
from typing import Literal

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
from mlcroissant._src.core.uuid import uuid_from_jsonld
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.source import Source


@dataclasses.dataclass(kw_only=True)
class Property:
    python: str
    jsonld: term.URIRef
    cardinality: Literal["ONE", "MANY"]
    description: str = ""
    mandatory: bool = False


@dataclasses.dataclass(eq=False, repr=False)
class FileObject(Node):
    """Nodes to describe a dataset FileObject (distribution)."""

    content_url: str | None = None
    content_size: str | None = None
    contained_in: list[str] | None = None
    description: str | None = None
    encoding_format: str | None = None
    md5: str | None = None
    name: str = ""
    same_as: list[str] | None = None
    sha256: str | None = None
    source: Source | None = None

    def __post_init__(self):
        """Checks arguments of the node."""
        # We could do extra validation by going through cls.PROPERTIES.
        self.validate_name()
        for _property in self.__class__.PROPERTIES(self.ctx):
            if _property.mandatory:
                self.assert_has_mandatory_properties(_property.python)
        if not self.contained_in:
            self.assert_has_mandatory_properties("content_url")
            if self.ctx and not self.ctx.is_live_dataset:
                self.assert_has_exclusive_properties(["md5", "sha256"])

    @classmethod
    def PROPERTIES(cls, ctx: Context) -> list[Property]:
        return [
            Property(
                description=(
                    "The name of the file.  As much as possible, the name should"
                    " reflect the name of the file as downloaded, including the file"
                    " extension. e.g. “images.zip”."
                ),
                python="name",
                jsonld=SDO.name,
                cardinality="ONE",
                mandatory=True,
            ),
            Property(python="description", jsonld=SDO.description, cardinality="ONE"),
            Property(
                description=(
                    "File size in (mega/kilo/…)bytes. Defaults to bytes if a unit is"
                    " not specified."
                ),
                python="content_size",
                jsonld=SDO.contentSize,
                cardinality="ONE",
            ),
            Property(
                description=(
                    "Actual bytes of the media object, for example the image file or"
                    " video file."
                ),
                python="content_url",
                jsonld=SDO.contentUrl,
                cardinality="ONE",
            ),
            Property(
                description=(
                    "Another FileObject or FileSet that this one is contained in, e.g.,"
                    " in the case of a file extracted from an archive. When this"
                    " property is present, the contentUrl is evaluated as a relative"
                    " path within the container object"
                ),
                python="contained_in",
                jsonld=SDO.containedIn,
                cardinality="MANY",
            ),
            Property(
                description="The format of the file, given as a mime type.",
                python="encoding_format",
                jsonld=SDO.encodingFormat,
                cardinality="ONE",
                mandatory=True,
            ),
            Property(
                python="md5",
                jsonld=ML_COMMONS(ctx).md5,
                cardinality="ONE",
            ),
            Property(
                description=(
                    "URL (or local name) of a FileObject with the same content, but in"
                    " a different format."
                ),
                python="same_as",
                jsonld=SDO.sameAs,
                cardinality="MANY",
            ),
            Property(
                description="Checksum for the file contents.",
                python="sha256",
                jsonld=SDO.sha256,
                cardinality="ONE",
            ),
            Property(
                python="source",
                jsonld=ML_COMMONS(ctx).source,
                cardinality="ONE",
            ),
        ]

    @classmethod
    def JSONLD_TYPE(cls, ctx: Context):
        return constants.SCHEMA_ORG_FILE_OBJECT(ctx)

    # This method would move to `Node`, as it's now generic.
    def to_json(self) -> Json:
        """Converts the `FileObject` to JSON."""
        cls = self.__class__
        jsonld = {
            "@type": self.ctx.rdf.shorten_value(cls.JSONLD_TYPE(self.ctx)),
        }
        for property in cls.PROPERTIES(self.ctx):
            key = property.jsonld.split("/")[-1]
            value = getattr(self, property.python)
            if value and hasattr(value, "to_json"):
                value = value.to_json()
            if property.cardinality == "MANY":
                value = unbox_singleton_list(value)
            jsonld[key] = value
        return remove_empty_values(jsonld)

    # This method would move to `Node`, as it's now generic.
    @classmethod
    def from_jsonld(
        cls,
        ctx: Context,
        jsonld: Json,
    ) -> FileObject:
        """Creates a `FileObject` from JSON-LD."""
        check_expected_type(ctx, jsonld, cls.JSONLD_TYPE(ctx))
        kwargs = {}
        for _property in cls.PROPERTIES(ctx):
            key = _property.python
            value = jsonld.get(_property.jsonld)
            if _property.cardinality == "MANY":
                value = box_singleton_list(value)
            if value:
                kwargs[key] = value
        return cls(
            ctx=ctx,
            uuid=uuid_from_jsonld(jsonld),
            **kwargs,
        )
