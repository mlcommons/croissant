"""Field module."""

from __future__ import annotations

import dataclasses

from rdflib import term
from rdflib.namespace import SDO

from mlcroissant._src.core import constants
from mlcroissant._src.core import dataclasses as mlc_dataclasses
from mlcroissant._src.core.constants import DataType
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.data_types import EXPECTED_DATA_TYPES
from mlcroissant._src.core.json_ld import remove_empty_values
from mlcroissant._src.core.types import Json
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.source import Source


def _data_types_from_jsonld(ctx: Context, data_types: Json):
    if isinstance(data_types, dict):
        return data_types.get("@id")
    elif isinstance(data_types, (str, term.URIRef)):
        return term.URIRef(data_types)
    elif isinstance(data_types, list):
        return [_data_types_from_jsonld(ctx, d) for d in data_types]
    return []


def _data_types_to_jsonld(ctx: Context, data_types: list[term.URIRef] | None):
    if data_types:
        return [ctx.rdf.shorten_value(data_type) for data_type in data_types]
    return None


@dataclasses.dataclass(frozen=True, repr=False)
class ParentField:
    """Class for the `parentField` property."""

    references: Source | None = None
    source: Source | None = None

    @classmethod
    def from_jsonld(cls, ctx: Context, json_) -> ParentField | None:
        """Creates a `ParentField` from JSON-LD."""
        if json_ is None:
            return None
        references = json_.get(constants.ML_COMMONS_REFERENCES(ctx))
        source = json_.get(constants.ML_COMMONS_SOURCE(ctx))
        return cls(
            references=Source.from_jsonld(ctx, references),
            source=Source.from_jsonld(ctx, source),
        )

    def to_json(self, ctx: Context) -> Json:
        """Converts the `ParentField` to JSON."""
        return remove_empty_values({
            "references": self.references.to_json(ctx=ctx) if self.references else None,
            "source": self.source.to_json(ctx=ctx) if self.source else None,
        })


@mlc_dataclasses.dataclass
class Field(Node):
    """Nodes to describe a dataset Field."""

    description: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.SCHEMA_ORG_DESCRIPTION,
    )
    # `data_types` is different than `node.data_type`. See `data_type`'s docstring.
    data_types: list[term.URIRef] | None = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description=(
            "The data type of the field, identified by the URI of the corresponding"
            " class. It could be either an atomic type (e.g, `sc:Integer`) or a"
            " semantic type (e.g., `sc:GeoLocation`)."
        ),
        from_jsonld=_data_types_from_jsonld,
        input_types=[SDO.URL],
        to_jsonld=_data_types_to_jsonld,
        url=constants.ML_COMMONS_DATA_TYPE,
    )
    is_enumeration: bool | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Boolean],
        url=constants.ML_COMMONS_IS_ENUMERATION,
    )
    name: str = mlc_dataclasses.jsonld_field(
        default="",
        input_types=[SDO.Text],
        url=constants.SCHEMA_ORG_NAME,
    )
    parent_field: ParentField | None = mlc_dataclasses.jsonld_field(
        default=None,
        description=(
            "A special case of `SubField` that should be hidden because it references a"
            " `Field` that already appears in the `RecordSet`."
        ),
        from_jsonld=ParentField.from_jsonld,
        input_types=[ParentField],
        to_jsonld=lambda ctx, parent_field: parent_field.to_json(ctx),
        url=constants.ML_COMMONS_PARENT_FIELD,
    )
    references: Source = mlc_dataclasses.jsonld_field(
        default_factory=Source,
        description=(
            "Another `Field` of another `RecordSet` that this field references. This is"
            " the equivalent of a foreign key reference in a relational database."
        ),
        from_jsonld=Source.from_jsonld,
        input_types=[Source],
        to_jsonld=lambda ctx, source: source.to_json(ctx),
        url=constants.ML_COMMONS_REFERENCES,
    )
    repeated: bool | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="If true, then the Field is a list of values of type dataType.",
        input_types=[SDO.Boolean],
        url=constants.ML_COMMONS_REPEATED,
    )
    source: Source = mlc_dataclasses.jsonld_field(
        default_factory=Source,
        description=(
            "The data source of the field. This will generally reference a `FileObject`"
            " or `FileSet`'s contents (e.g., a specific column of a table)."
        ),
        from_jsonld=Source.from_jsonld,
        input_types=[Source],
        to_jsonld=lambda ctx, source: source.to_json(ctx),
        url=constants.ML_COMMONS_SOURCE,
    )
    sub_fields: list[Field] = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description="Another `Field` that is nested inside this one.",
        from_jsonld=lambda ctx, fields: Field.from_jsonld(ctx, fields),
        input_types=["Field"],
        to_jsonld=lambda ctx, fields: [field.to_json() for field in fields],
        url=constants.ML_COMMONS_SUB_FIELD,
    )

    def __post_init__(self):
        """Checks arguments of the node."""
        uuid_field = "name" if self.ctx.is_v0() else "id"
        self.validate_name()
        self.assert_has_mandatory_properties(uuid_field)
        self.assert_has_optional_properties("description")
        self.source.check_source(self.add_error)
        self._standardize_data_types()

    JSONLD_TYPE = constants.ML_COMMONS_FIELD_TYPE

    def _standardize_data_types(self):
        """Converts data_types to a list of rdflib.URIRef."""
        data_types = self.data_types
        if data_types is None:
            data_types = []
        if not isinstance(data_types, list):
            data_types = [data_types]
        self.data_types = [term.URIRef(data_type) for data_type in data_types]

    @property
    def data_type(self) -> type | term.URIRef | None:
        """Recursively retrieves the actual data type of the node.

        The data_type can be either directly on the node (`data_type`) or on one
        of the parent fields.

        `data_types` may contain semantic meaning, but `data_type` is the actual
        programmatic data type (i.e., bool, str, etc).
        """
        if self.sub_fields:
            return None
        data_types = self.data_types or []
        for data_type in data_types:
            # data_type can be matched to a Python type:
            if data_type in EXPECTED_DATA_TYPES:
                return EXPECTED_DATA_TYPES[term.URIRef(data_type)]
            # data_type is an ML semantic type:
            elif data_type in [
                DataType.IMAGE_OBJECT,
                # For some reasons, pytype cannot infer `Any` on ctx:
                DataType.BOUNDING_BOX(self.ctx),  # pytype: disable=wrong-arg-types
                DataType.AUDIO_OBJECT,
            ]:
                return term.URIRef(data_type)
        # The data_type has to be found on the source:
        source = self.ctx.node_by_uuid(self.source.uuid)
        if not isinstance(source, Field):
            self.add_error(
                "The field does not specify a valid"
                f" {constants.ML_COMMONS_DATA_TYPE(self.ctx)}, neither does any of"
                f" its predecessor. Got: {self.data_types}"
            )
            return None
        return source.data_type

    @property
    def data(self) -> str | None:
        """The data of the parent RecordSet."""
        if hasattr(self.parent, "data"):
            return getattr(self.parent, "data")
        return None
