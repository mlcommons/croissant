"""Utils to overload Python built-in dataclasses.

This module implements https://peps.python.org/pep-0681.
"""

from __future__ import annotations

from collections.abc import Iterator
from collections.abc import Mapping
from collections.abc import Sequence
import dataclasses
import inspect
from typing import Any, Callable, cast, Literal, TypedDict, Union

from rdflib import term
from rdflib.namespace import SDO
from typing_extensions import dataclass_transform

from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.core.types import Json

MATCHING_TYPES: Mapping[term.URIRef, type] = {
    SDO.Boolean: bool,
    SDO.Date: str,
    SDO.DateTime: str,
    SDO.Integer: int,
    SDO.Language: str,
    SDO.Number: float,
    SDO.Text: str,
    SDO.Time: str,
    SDO.URL: str,
}


class Metadata(TypedDict):
    """Interface for the metadata mapping.

    Arguments:
        cardinality: The RDF cardinality ("ONE" or "MANY").
        cast_fn: A function to apply in the __init__ that will cast the input value to
            a value with the expected type by the dataclass.
        description: The description of the field.
        exclusive_with: List of all fields the current field should be exclusive with,
            i.e. they cannot be both set at the same time.
        from_jsonld: A function to overwrite the parsing JSON-LD->Python.
        to_jsonld: A function to overwrite the parsing Python->JSON-LD.
        required: Whether the field is required.
        url: The RDF URL for the field or a function that takes into input the context
            (ctx) and outputs the RDF URL for the field.
        versions: The list/set of Croissant versions for which this field is used (by
            default all versions).
    """

    cardinality: Literal["ONE", "MANY"]
    cast_fn: Callable[[Any], Any] | None
    description: str
    exclusive_with: Sequence[str]
    from_jsonld: Callable[[Context, Json], Any] | None
    input_types: list[term.URIRef | type]
    to_jsonld: Callable[[Context, Any], Json] | None
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
    def cast_fn(self):
        """Getter for cast_fn."""
        return self.metadata.get("cast_fn")

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
    cast_fn=None,
    description="",
    exclusive_with=None,
    from_jsonld=None,
    input_types=None,
    to_jsonld=None,
    url=None,
    versions=None,
    **kwargs,
):
    """Overloads dataclasses.field with specific attributes."""
    if cardinality not in ["ONE", "MANY"]:
        raise ValueError(f"cardinality should be ONE or MANY. Got {cardinality}")
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
            cast_fn=cast_fn,
            description=description,
            exclusive_with=exclusive_with,
            from_jsonld=from_jsonld,
            input_types=input_types,
            to_jsonld=to_jsonld,
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
        metadata = cast(Metadata, field.metadata)
        if metadata:
            _check_types(cls_or_instance, field, metadata)
            yield JsonldField(
                default=field.default,
                default_factory=field.default_factory,
                name=field.name,
                metadata=metadata,
            )


@dataclass_transform(
    field_specifiers=(jsonld_field,)
)  # pytype: disable=not-supported-yet
def dataclass(cls):
    """Overloads the built-in dataclass with JsonldFields instead of Fields."""
    return dataclasses.dataclass(eq=False, repr=False)(cls)


def _check_types(cls_or_instance, field: dataclasses.Field, metadata: Metadata) -> None:
    """Checks that the JSON-LD types confirm to the Python types for cls_or_instance."""
    metadata = Metadata(**metadata)
    input_types = metadata["input_types"]
    cls_name = (
        cls_or_instance.__name__
        if isinstance(cls_or_instance, type)
        else cls_or_instance.__class__.__name__
    )
    field_name = f'"{cls_name}.{field.name}"'
    if not input_types:
        # No heuristic is possible as input_types were not specified:
        return
    types: list[type] = []
    for input_type in input_types:
        if isinstance(input_type, term.URIRef):
            if input_type in MATCHING_TYPES:
                types.append(MATCHING_TYPES[input_type])
            else:
                raise ValueError(f"input_type={input_type} has no matching type.")
        else:
            types.append(input_type)
    expected_type = Union[tuple(types)]  # type: ignore
    if metadata["cardinality"] == "MANY":
        expected_type = list[expected_type]  # type: ignore
    if field.default != dataclasses.MISSING:
        expected_type = Union[expected_type, type(field.default)]  # type: ignore

    cast_fn = metadata["cast_fn"]
    if cast_fn:
        # The field defines cast_fn: we check that Python type == cast_fn output type.
        signature = inspect.signature(cast_fn)
        name = f"{field_name} with cast_fn={cast_fn.__name__}"
        _types_are_equal(name, field.type, signature.return_annotation)
    else:
        # Python type == expected JSON-LD type.
        _types_are_equal(field_name, field.type, expected_type)


def _types_are_equal(field_name: str, type1: Any, type2: Any) -> None:
    if type1 != type2:
        raise TypeError(f"Field {field_name} should have type {type2}. Got {type1}")
