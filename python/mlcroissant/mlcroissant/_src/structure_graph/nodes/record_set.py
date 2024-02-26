"""RecordSet module."""

from __future__ import annotations

import dataclasses
import itertools
import json

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.data_types import check_expected_type
from mlcroissant._src.core.issues import ValidationError
from mlcroissant._src.core.json_ld import remove_empty_values
from mlcroissant._src.core.types import Json
from mlcroissant._src.core.uuid import uuid_from_jsonld
from mlcroissant._src.core.uuid import uuid_to_jsonld
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.field import Field


@dataclasses.dataclass(eq=False, repr=False)
class RecordSet(Node):
    """Nodes to describe a dataset RecordSet."""

    # `data` is passed as a string for the moment, because dicts and lists are not
    # hashable.
    data: list[Json] | None = None
    description: str | None = None
    is_enumeration: bool | None = None
    key: str | list[str] | None = None
    name: str = ""
    id: str = ""  # JSON-LD @id
    fields: list[Field] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        """Checks arguments of the node."""
        self.validate_name()
        self.assert_has_mandatory_properties("name", "id")
        self.assert_has_optional_properties("description")

        if self.data is not None:
            data = self.data
            if not isinstance(data, list):
                self.add_error(
                    f"{constants.ML_COMMONS_DATA(self.ctx)} should declare a list. Got:"
                    f" {type(data)}."
                )
                return
            if not data:
                self.add_error(
                    f"{constants.ML_COMMONS_DATA(self.ctx)} should declare a non empty"
                    " list."
                )
            expected_keys = {field.name for field in self.fields}
            for i, line in enumerate(data):
                if not isinstance(line, dict):
                    self.add_error(
                        f"{constants.ML_COMMONS_DATA(self.ctx)} should declare a list"
                        f" of dict. Got: a list of {type(line)}."
                    )
                    return
                keys = set(line.keys())
                if keys != expected_keys:
                    self.add_error(
                        f"Line #{i} doesn't have the expected columns. Expected:"
                        f" {expected_keys}. Got: {keys}."
                    )

    def to_json(self) -> Json:
        """Converts the `RecordSet` to JSON."""
        prefix = "ml" if self.ctx.is_v0() else "cr"
        json_output = remove_empty_values({
            "@type": f"{prefix}:RecordSet",
            "@id": uuid_to_jsonld(self.uuid),
            "name": self.name,
            "description": self.description,
            "isEnumeration": self.is_enumeration,
            "key": self.key,
            "field": [field.to_json() for field in self.fields],
            "data": self.data,
        })
        if self.ctx.is_v0():
            json_output.pop("@id")
        return json_output

    @classmethod
    def from_jsonld(cls, ctx: Context, record_set: Json) -> RecordSet:
        """Creates a `RecordSet` from JSON-LD."""
        check_expected_type(
            ctx.issues, record_set, constants.ML_COMMONS_RECORD_SET_TYPE(ctx)
        )
        record_set_name = record_set.get(constants.SCHEMA_ORG_NAME, "")
        fields = record_set.pop(constants.ML_COMMONS_FIELD(ctx), [])
        if isinstance(fields, dict):
            fields = [fields]
        fields = [Field.from_jsonld(ctx, field) for field in fields]
        key = record_set.get(constants.SCHEMA_ORG_KEY(ctx))
        data = record_set.get(constants.ML_COMMONS_DATA(ctx))
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.decoder.JSONDecodeError:
                data = None
                ctx.issues.add_error(
                    f"{constants.ML_COMMONS_DATA(ctx)} is not a proper list of JSON:"
                    f" {data}"
                )
        is_enumeration = record_set.get(constants.ML_COMMONS_IS_ENUMERATION(ctx))
        return cls(
            ctx=ctx,
            data=data,
            description=record_set.get(constants.SCHEMA_ORG_DESCRIPTION),
            is_enumeration=is_enumeration,
            key=key,
            fields=fields,
            name=record_set_name,
            id=uuid_from_jsonld(record_set),
        )

    def check_joins_in_fields(self):
        """Checks that all joins are declared when they are consumed."""
        joins: set[tuple[str, str]] = set()
        sources: set[str] = set()
        for field in self.fields:
            source_uuid = field.source.uuid
            references_uuid = field.references.uuid
            if source_uuid:
                # source_uuid is used as a source.
                sources.add(get_parent_uuid(self.ctx, source_uuid))
            if source_uuid and references_uuid:
                # A join happens because the user specified `source` and `references`.
                joins.add(
                    (
                        get_parent_uuid(self.ctx, source_uuid),
                        get_parent_uuid(self.ctx, references_uuid),
                    )
                )
                joins.add(
                    (
                        get_parent_uuid(self.ctx, references_uuid),
                        get_parent_uuid(self.ctx, source_uuid),
                    )
                )
        for combination in itertools.combinations(sources, 2):
            if combination not in joins:
                # Sort for reproducibility.
                ordered_combination = tuple(
                    sorted([uuid_to_jsonld(source) for source in combination])
                )
                self.add_error(
                    f"You try to use the sources with names {ordered_combination} as"
                    " sources, but you didn't declare a join between them. Use"
                    " `ml:references` to declare a join. Please, refer to the"
                    " documentation for more information."
                )


def get_parent_uuid(ctx: Context, uuid: str) -> str:
    """Retrieves the UID of the parent, e.g. `file/column` -> `file`."""
    # TODO: rename this function and have better error message.
    node = ctx.node_by_uuid(uuid)
    if node is None:
        raise ValidationError(
            "Found the following 1 error(s) during the validation:\n  -  Node with"
            f" uuid={uuid_to_jsonld(uuid)} does not exist. This error might have been"
            " found during a Join operation."
        )
    if isinstance(node, Field):
        if node.parent:
            return node.parent.uuid
    return node.uuid
