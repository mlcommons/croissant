"""Field module."""

from __future__ import annotations

import dataclasses

from rdflib import term

from mlcroissant._src.core import constants
from mlcroissant._src.core.constants import DataType
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.data_types import check_expected_type
from mlcroissant._src.core.data_types import EXPECTED_DATA_TYPES
from mlcroissant._src.core.json_ld import remove_empty_values
from mlcroissant._src.core.types import Json
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.source import Source


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

    def to_json(self) -> Json:
        """Converts the `ParentField` to JSON."""
        return remove_empty_values({
            "references": self.references.to_json() if self.references else None,
            "source": self.source.to_json() if self.source else None,
        })


@dataclasses.dataclass(eq=False, repr=False)
class Field(Node):
    """Nodes to describe a dataset Field."""

    description: str | None = None
    # `data_types` is different than `node.data_type`. See `data_type`'s docstring.
    data_types: term.URIRef | list[term.URIRef] = dataclasses.field(  # type: ignore  # https://github.com/python/mypy/issues/11923
        default_factory=list
    )
    is_enumeration: bool | None = None
    name: str = ""
    parent_field: ParentField | None = None
    references: Source = dataclasses.field(default_factory=Source)
    repeated: bool | None = None
    source: Source = dataclasses.field(default_factory=Source)
    sub_fields: list[Field] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        """Checks arguments of the node."""
        self.validate_name()
        self.assert_has_mandatory_properties("name")
        self.assert_has_optional_properties("description")
        self.source.check_source(self.add_error)
        self._standardize_data_types()

    def _standardize_data_types(self):
        """Converts data_types to a list of rdflib.URIRef."""
        if self.data_types is None:
            self.data_types = []
        if not isinstance(self.data_types, list):
            self.data_types = [self.data_types]
        self.data_types = [term.URIRef(data_type) for data_type in self.data_types]

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
        if self.data_types is not None:
            for data_type in self.data_types:
                # data_type can be matched to a Python type:
                if data_type in EXPECTED_DATA_TYPES:
                    return EXPECTED_DATA_TYPES[term.URIRef(data_type)]
                # data_type is an ML semantic type:
                elif data_type in [
                    DataType.IMAGE_OBJECT,
                    # For some reasons, pytype cannot infer `Any` on ctx:
                    DataType.BOUNDING_BOX(self.ctx),  # pytype: disable=wrong-arg-types
                ]:
                    return term.URIRef(data_type)
        # The data_type has to be found on a predecessor:
        predecessor = next((p for p in self.predecessors if isinstance(p, Field)), None)
        if predecessor is None:
            self.add_error(
                "The field does not specify a valid"
                f" {constants.ML_COMMONS_DATA_TYPE(self.ctx)}, neither does any of its"
                f" predecessor. Got: {self.data_types}"
            )
            return None
        return predecessor.data_type

    @property
    def data(self) -> str | None:
        """The data of the parent RecordSet."""
        if hasattr(self.parent, "data"):
            return getattr(self.parent, "data")
        return None

    def to_json(self) -> Json:
        """Converts the `Field` to JSON."""
        data_types = [
            self.ctx.rdf.shorten_value(data_type) for data_type in self.data_types
        ]
        parent_field = self.parent_field.to_json() if self.parent_field else None
        prefix = "ml" if self.ctx.is_v0() else "cr"
        return remove_empty_values({
            "@type": f"{prefix}:Field",
            "name": self.name,
            "description": self.description,
            "dataType": data_types[0] if len(data_types) == 1 else data_types,
            "isEnumeration": self.is_enumeration,
            "parentField": parent_field,
            "repeated": self.repeated,
            "references": self.references.to_json() if self.references else None,
            "source": self.source.to_json() if self.source else None,
            "subField": [sub_field.to_json() for sub_field in self.sub_fields],
        })

    @classmethod
    def from_jsonld(cls, ctx: Context, field: Json) -> Field:
        """Creates a `Field` from JSON-LD."""
        check_expected_type(
            ctx.issues,
            field,
            constants.ML_COMMONS_FIELD_TYPE(ctx),
        )
        references_jsonld = field.get(constants.ML_COMMONS_REFERENCES(ctx))
        references = Source.from_jsonld(ctx, references_jsonld)
        source_jsonld = field.get(constants.ML_COMMONS_SOURCE(ctx))
        source = Source.from_jsonld(ctx, source_jsonld)
        data_types = field.get(constants.ML_COMMONS_DATA_TYPE(ctx), [])
        is_enumeration = field.get(constants.ML_COMMONS_IS_ENUMERATION(ctx))
        if isinstance(data_types, dict):
            data_types = [data_types.get("@id")]
        elif isinstance(data_types, list):
            data_types = [d.get("@id") for d in data_types]
        else:
            data_types = []
        field_name = field.get(constants.SCHEMA_ORG_NAME, "")
        sub_fields = field.get(constants.ML_COMMONS_SUB_FIELD(ctx), [])
        if isinstance(sub_fields, dict):
            sub_fields = [sub_fields]
        sub_fields = [Field.from_jsonld(ctx, sub_field) for sub_field in sub_fields]
        parent_field = ParentField.from_jsonld(
            ctx, field.get(constants.ML_COMMONS_PARENT_FIELD(ctx))
        )
        repeated = field.get(constants.ML_COMMONS_REPEATED(ctx))
        return cls(
            ctx=ctx,
            description=field.get(constants.SCHEMA_ORG_DESCRIPTION),
            data_types=data_types,
            is_enumeration=is_enumeration,
            name=field_name,
            parent_field=parent_field,
            references=references,
            repeated=repeated,
            source=source,
            sub_fields=sub_fields,
        )
