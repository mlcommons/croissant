"""RecordSet module."""

import itertools
import json

from rdflib import term
from rdflib.namespace import SDO

from mlcroissant._src.core import constants
from mlcroissant._src.core import dataclasses as mlc_dataclasses
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.data_types import data_types_from_jsonld
from mlcroissant._src.core.data_types import data_types_to_jsonld
from mlcroissant._src.core.types import Json
from mlcroissant._src.core.uuid import formatted_uuid_to_json
from mlcroissant._src.core.uuid import uuid_from_jsonld
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.base_node import node_by_uuid
from mlcroissant._src.structure_graph.nodes.field import Field


def json_from_jsonld(ctx: Context, data) -> Json | None:
    """Creates `data` from a JSON-LD fragment."""
    if isinstance(data, str):
        try:
            return json.loads(data)
        except json.decoder.JSONDecodeError:
            ctx.issues.add_error(
                f"{constants.ML_COMMONS_DATA(ctx)} is not a proper list of JSON: {data}"
            )
    return None


@mlc_dataclasses.dataclass
class RecordSet(Node):
    """Nodes to describe a dataset RecordSet."""

    JSONLD_TYPE = constants.ML_COMMONS_RECORD_SET_TYPE

    data: list[Json] | None = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default=None,
        description="One or more records that constitute the data of the `RecordSet`.",
        from_jsonld=json_from_jsonld,
        url=constants.ML_COMMONS_DATA,
    )
    data_types: list[term.URIRef] | None = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description=(
            "The data type of the RecordSet. Mainly used to specify: `sc:Enumeration`."
        ),
        from_jsonld=data_types_from_jsonld,
        to_jsonld=data_types_to_jsonld,
        url=constants.ML_COMMONS_DATA_TYPE,
    )
    description: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.SCHEMA_ORG_DESCRIPTION,
    )
    examples: list[Json] | None = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default=None,
        description=(
            "One or more records provided as example content of the `RecordSet`, or a"
            " reference to data source that contains examples."
        ),
        from_jsonld=json_from_jsonld,
        url=constants.ML_COMMONS_EXAMPLES,
    )
    is_enumeration: bool | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Boolean],
        url=constants.ML_COMMONS_IS_ENUMERATION,
    )
    key: list[str] | None = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default=None,
        description=(
            "One or more fields whose values uniquely identify each record in the"
            " `RecordSet`."
        ),
        from_jsonld=lambda ctx, jsonld: uuid_from_jsonld(jsonld),
        to_jsonld=formatted_uuid_to_json,
        url=constants.SCHEMA_ORG_KEY,
    )
    name: str = mlc_dataclasses.jsonld_field(
        default="",
        description="The name of the RecordSet.",
        input_types=[SDO.Text],
        url=constants.SCHEMA_ORG_NAME,
    )
    fields: list[Field] = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description=(
            "A data element that appears in the records of the RecordSet (e.g., one"
            " column of a table)."
        ),
        input_types=[Field],
        url=constants.ML_COMMONS_FIELD,
    )

    def __post_init__(self):
        """Checks arguments of the node."""
        Node.__post_init__(self)
        uuid_field = "name" if self.ctx.is_v0() else "id"
        self.validate_name()
        self.assert_has_mandatory_properties(uuid_field)

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
            if self.ctx.is_v0():
                expected_keys = {field.name for field in self.fields}
            else:
                expected_keys = {field.id for field in self.fields}
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
        sources: set[str | None] = set()
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


def get_parent_uuid(ctx: Context, uuid: str) -> str | None:
    """Retrieves the UID of the parent, e.g. `file/column` -> `file`."""
    node = node_by_uuid(ctx, uuid)
    if node is None:
        ctx.issues.add_error(
            f"Node with uuid={uuid} does not exist. This error might have been found"
            " during a Join operation."
        )
        return None
    if isinstance(node, Field):
        if node.parent:
            return node.parent.uuid
    return node.uuid
