"""Utils to overload Python built-in dataclasses.

This module implements https://peps.python.org/pep-0681.
"""

from __future__ import annotations

from collections.abc import Iterator
from collections.abc import Sequence
import dataclasses
from typing import Any, Callable, Literal, TypedDict

from rdflib import term
from typing_extensions import dataclass_transform

from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.core.types import Json


class Metadata(TypedDict):
    """Interface for the metadata mapping."""

    cardinality: Literal["ONE", "MANY"]
    description: str
    exclusive_with: Sequence[str]
    from_jsonld: Callable[[Context, Json], Any] | None
    input_types: list[term.URIRef | type]
    to_jsonld: Callable[[Context, Any], Json] | None
    required: bool
    url: term.URIRef | Callable[[Context], term.URIRef]
    versions: set[CroissantVersion] | list[CroissantVersion]


@dataclasses.dataclass
class JsonldField:
    """Overloads dataclasses.Field with JSON-LD-specific attributes."""

    default: Any
    default_factory: Any
    name: str
    metadata: Metadata

    @property
    def cardinality(self):
        """Getter for cardinality."""
        return self.metadata.get("cardinality")

    @property
    def description(self):
        """Getter for description."""
        return self.metadata.get("description")

    @property
    def exclusive_with(self):
        """Getter for exclusive_with."""
        return self.metadata.get("exclusive_with")

    @property
    def from_jsonld(self):
        """Getter for from_jsonld."""
        return self.metadata.get("from_jsonld")

    @property
    def input_types(self):
        """Getter for input_types."""
        return self.metadata.get("input_types", [])

    @property
    def to_jsonld(self):
        """Getter for to_jsonld."""
        return self.metadata.get("to_jsonld")

    @property
    def required(self):
        """Getter for required."""
        return self.metadata.get("required")

    @property
    def url(self):
        """Getter for url."""
        return self.metadata.get("url")

    @property
    def versions(self):
        """Getter for versions."""
        return self.metadata.get("versions")

    def call_from_jsonld(self, ctx: Context, value: Any):
        """Calls `from_jsonld` in the field."""
        if value and self.from_jsonld:
            return self.from_jsonld(ctx, value)
        else:
            return value

    def call_to_jsonld(self, ctx: Context, value: Any):
        """Calls `to_jsonld` in the field."""
        if value and self.to_jsonld:
            return self.to_jsonld(ctx, value)
        else:
            return value

    def call_url(self, ctx: Context) -> term.URIRef:
        """Calls `jsonld` in the field."""
        url = self.url
        if callable(url):
            return url(ctx)
        else:
            return url


def jsonld_field(
    cardinality="ONE",
    description="",
    exclusive_with=None,
    from_jsonld=None,
    input_types=None,
    to_jsonld=None,
    required=False,
    url=None,
    versions=None,
    **kwargs,
):
    """Overloads dataclasses.field with specific attributes."""
    if input_types is None:
        input_types = []
    if exclusive_with is None:
        exclusive_with = []
    if versions is None:
        versions = set(CroissantVersion)  # All versions are supported by default
    if not from_jsonld and not input_types:
        raise ValueError("You should specify either `from_jsonld` or `input_types`.")
    elif from_jsonld and input_types:
        raise ValueError("You can only specify either `from_jsonld` or `input_types`.")
    return dataclasses.field(
        metadata=Metadata(
            cardinality=cardinality,
            description=description,
            exclusive_with=exclusive_with,
            from_jsonld=from_jsonld,
            input_types=input_types,
            to_jsonld=to_jsonld,
            required=required,
            url=url,
            versions=versions,
        ),
        **kwargs,
    )


def jsonld_fields(cls_or_instance) -> Iterator[JsonldField]:
    """Filters the JSON-LD fields."""
    for field in dataclasses.fields(cls_or_instance):
        if hasattr(cls_or_instance, "ctx"):
            ctx = getattr(cls_or_instance, "ctx")
            versions = field.metadata.get("versions") or set()
            if isinstance(ctx, Context) and ctx.conforms_to not in versions:
                # The field is not to be used with the current version of Croissant:
                continue
        if field.metadata:
            yield JsonldField(default=field.default, default_factory=field.default_factory, name=field.name, metadata=field.metadata)  # type: ignore


@dataclass_transform(
    field_specifiers=(jsonld_field,)
)  # pytype: disable=not-supported-yet
def dataclass(cls):
    """Overloads the built-in dataclass with JsonldFields instead of Fields."""
    return dataclasses.dataclass(eq=False, repr=False)(cls)
