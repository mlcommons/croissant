"""RecordSet module."""

from __future__ import annotations

import dataclasses
import itertools
import json

from rdflib.namespace import SDO

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.dataclasses import jsonld_field
from mlcroissant._src.core.dataclasses import JsonldField
from mlcroissant._src.core.types import Json
from mlcroissant._src.structure_graph.base_node import NodeV2
from mlcroissant._src.structure_graph.nodes.field import Field

OriginalField = dataclasses.Field
dataclasses.Field = JsonldField  # type: ignore


def data_from_jsonld(ctx: Context, data) -> Json | None:
    """Creates `data` from a JSON-LD fragment."""
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.decoder.JSONDecodeError:
            ctx.issues.add_error(
                f"{constants.ML_COMMONS_DATA(ctx)} is not a proper list of JSON: {data}"
            )
    return None


@dataclasses.dataclass(eq=False, repr=False)
class RecordSet(NodeV2):
    """Nodes to describe a dataset RecordSet."""

    # pytype: disable=annotation-type-mismatch
    data: list[Json] | None = jsonld_field(
        cardinality="MANY",
        default=None,
        description="One or more records that constitute the data of the `RecordSet`.",
        from_jsonld=data_from_jsonld,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_DATA,
    )
    description: str | None = jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.SCHEMA_ORG_DESCRIPTION,
    )
    is_enumeration: bool | None = jsonld_field(
        default=None,
        input_types=[SDO.Boolean],
        url=constants.ML_COMMONS_IS_ENUMERATION,
    )
    key: str | list[str] | None = jsonld_field(
        cardinality="MANY",
        default=None,
        description=(
            "One or more fields whose values uniquely identify each record in the"
            " `RecordSet`."
        ),
        input_types=[SDO.Text],
        url=constants.SCHEMA_ORG_KEY,
    )
    name: str = jsonld_field(
        default="",
        input_types=[SDO.Text],
        url=constants.SCHEMA_ORG_NAME,
    )
    fields: list[Field] = jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description=(
            "A data element that appears in the records of the RecordSet (e.g., one"
            " column of a table)."
        ),
        from_jsonld=Field.from_jsonld,
        input_types=[Field],
        to_jsonld=lambda ctx, fields: [field.to_json() for field in fields],
        url=constants.ML_COMMONS_FIELD,
    )
    # pytype: enable=annotation-type-mismatch

    def __post_init__(self):
        """Checks arguments of the node."""
        uuid_field = "name" if self.ctx.is_v0() else "id"
        self.validate_name()
        self.assert_has_mandatory_properties(uuid_field)
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
                ordered_combination = tuple(sorted(combination))
                self.add_error(
                    f"You try to use the sources with names {ordered_combination} as"
                    " sources, but you didn't declare a join between them. Use"
                    " `ml:references` to declare a join. Please, refer to the"
                    " documentation for more information."
                )

    @classmethod
    def _JSONLD_TYPE(cls, ctx: Context):
        """Gets the class' JSON-LD @type."""
        return constants.ML_COMMONS_RECORD_SET_TYPE(ctx)


def get_parent_uuid(ctx: Context, uuid: str) -> str:
    """Retrieves the UID of the parent, e.g. `file/column` -> `file`."""
    node = ctx.node_by_uuid(uuid)
    if node is None:
        ctx.issues.add_error(
            f"Node with uuid={uuid} does not exist. This error might have been found"
            " during a Join operation."
        )
    if isinstance(node, Field):
        if node.parent:
            return node.parent.uuid
    return node.uuid


dataclasses.Field = OriginalField  # type: ignore
