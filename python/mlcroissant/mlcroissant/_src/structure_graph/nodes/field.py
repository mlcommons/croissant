"""Field module."""

from __future__ import annotations

import dataclasses

from etils import epath

from mlcroissant._src.core import constants
from mlcroissant._src.core.data_types import check_expected_type
from mlcroissant._src.core.data_types import shorten_data_type
from mlcroissant._src.core.issues import Context
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.core.json_ld import remove_empty_values
from mlcroissant._src.core.types import Json
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.rdf import Rdf
from mlcroissant._src.structure_graph.nodes.source import Source


@dataclasses.dataclass(frozen=True, repr=False)
class ParentField:
    """Class for the `parentField` property."""

    references: Source | None = None
    source: Source | None = None

    @classmethod
    def from_jsonld(cls, issues: Issues, json_) -> ParentField | None:
        """Creates a `ParentField` from JSON-LD."""
        if json_ is None:
            return None
        references = json_.get(constants.ML_COMMONS_REFERENCES)
        source = json_.get(constants.ML_COMMONS_SOURCE)
        return cls(
            references=Source.from_jsonld(issues, references),
            source=Source.from_jsonld(issues, source),
        )

    def to_json(self) -> Json:
        """Converts the `ParentField` to JSON."""
        return remove_empty_values(
            {
                "references": self.references.to_json(),
                "source": self.source.to_json(),
            }
        )


@dataclasses.dataclass(eq=False, repr=False)
class Field(Node):
    """Nodes to describe a dataset Field."""

    description: str | None = None
    # `data_type` is different than `node.actual_data_type`. See `actual_data_type`.
    data_type: str | list[str] | None = None
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

    @property
    def actual_data_type(self) -> str | list[str] | None:
        """Recursively retrieves the actual data type of the node.

        The data_type can be either directly on the node (`data_type`) or on one
        of the parent fields.
        """
        if self.data_type is not None:
            return self.data_type
        parent = next(self.graph.predecessors(self), None)
        if parent is None or not isinstance(parent, Field):
            self.add_error(
                f"The field does not specify any {constants.ML_COMMONS_DATA_TYPE},"
                " neither does any of its predecessor."
            )
            return None
        return parent.actual_data_type

    @property
    def data(self) -> str | None:
        """The data of the parent RecordSet."""
        if hasattr(self.parent, "data"):
            return getattr(self.parent, "data")
        return None

    def to_json(self) -> Json:
        """Converts the `Field` to JSON."""
        data_type = shorten_data_type(self.rdf, self.data_type)
        parent_field = self.parent_field.to_json() if self.parent_field else None
        return remove_empty_values(
            {
                "@type": "ml:Field",
                "name": self.name,
                "description": self.description,
                "dataType": data_type,
                "isEnumeration": self.is_enumeration,
                "parentField": parent_field,
                "repeated": self.repeated,
                "references": self.references.to_json() if self.references else None,
                "source": self.source.to_json() if self.source else None,
                "subField": [sub_field.to_json() for sub_field in self.sub_fields],
            }
        )

    @classmethod
    def from_jsonld(
        cls,
        issues: Issues,
        context: Context,
        folder: epath.Path,
        rdf: Rdf,
        field: Json,
    ) -> Field:
        """Creates a `Field` from JSON-LD."""
        check_expected_type(
            issues,
            field,
            constants.ML_COMMONS_FIELD_TYPE,
        )
        references_jsonld = field.get(constants.ML_COMMONS_REFERENCES)
        references = Source.from_jsonld(issues, references_jsonld)
        source_jsonld = field.get(constants.ML_COMMONS_SOURCE)
        source = Source.from_jsonld(issues, source_jsonld)
        data_type = field.get(constants.ML_COMMONS_DATA_TYPE, {})
        is_enumeration = field.get(constants.ML_COMMONS_IS_ENUMERATION)
        if isinstance(data_type, dict):
            data_type = data_type.get("@id")
        elif isinstance(data_type, list):
            data_type = [d.get("@id") for d in data_type]
        else:
            data_type = None
        field_name = field.get(constants.SCHEMA_ORG_NAME, "")
        if context.field_name is None:
            context.field_name = field_name
        else:
            context.sub_field_name = field_name
        sub_fields = field.get(constants.ML_COMMONS_SUB_FIELD, [])
        if isinstance(sub_fields, dict):
            sub_fields = [sub_fields]
        sub_fields = [
            Field.from_jsonld(issues, context, folder, rdf, sub_field)
            for sub_field in sub_fields
        ]
        parent_field = ParentField.from_jsonld(
            issues, field.get(constants.ML_COMMONS_PARENT_FIELD)
        )
        repeated = field.get(constants.ML_COMMONS_REPEATED)
        return cls(
            issues=issues,
            context=context,
            folder=folder,
            description=field.get(constants.SCHEMA_ORG_DESCRIPTION),
            data_type=data_type,
            is_enumeration=is_enumeration,
            name=field_name,
            parent_field=parent_field,
            rdf=rdf,
            references=references,
            repeated=repeated,
            source=source,
            sub_fields=sub_fields,
        )
