"""Utils to overload Python built-in dataclasses."""

from __future__ import annotations

import dataclasses
from typing import Any, Callable, Literal

from rdflib import term

from mlcroissant._src.core.context import Context
from mlcroissant._src.core.types import Json


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
