"""RecordSet module."""

from __future__ import annotations

import dataclasses
import json

from etils import epath

from mlcroissant._src.core import constants
from mlcroissant._src.core.data_types import check_expected_type
from mlcroissant._src.core.issues import Context
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.core.json_ld import remove_empty_values
from mlcroissant._src.core.types import Json
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.rdf import Rdf


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
    fields: list[Field] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        """Checks arguments of the node."""
        self.validate_name()
        self.assert_has_mandatory_properties("name")
        self.assert_has_optional_properties("description")
        if self.data is not None:
            data = self.data
            if not isinstance(data, list):
                self.add_error(
                    f"{constants.ML_COMMONS_DATA} should declare a list. Got:"
                    f" {type(data)}."
                )
                return
            if not data:
                self.add_error(
                    f"{constants.ML_COMMONS_DATA} should declare a non empty list."
                )
            expected_keys = {field.name for field in self.fields}
            for i, line in enumerate(data):
                if not isinstance(line, dict):
                    self.add_error(
                        f"{constants.ML_COMMONS_DATA} should declare a list of dict."
                        f" Got: a list of {type(line)}."
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
        return remove_empty_values(
            {
                "@type": "ml:RecordSet",
                "name": self.name,
                "description": self.description,
                "isEnumeration": self.is_enumeration,
                "key": self.key,
                "field": [field.to_json() for field in self.fields],
                "data": self.data,
            }
        )

    @classmethod
    def from_jsonld(
        cls,
        issues: Issues,
        context: Context,
        folder: epath.Path,
        rdf: Rdf,
        record_set: Json,
    ) -> RecordSet:
        """Creates a `RecordSet` from JSON-LD."""
        check_expected_type(issues, record_set, constants.ML_COMMONS_RECORD_SET_TYPE)
        record_set_name = record_set.get(constants.SCHEMA_ORG_NAME, "")
        context = Context(
            dataset_name=context.dataset_name, record_set_name=record_set_name
        )
        fields = record_set.pop(constants.ML_COMMONS_FIELD, [])
        if isinstance(fields, dict):
            fields = [fields]
        fields = [
            Field.from_jsonld(issues, context, folder, rdf, field) for field in fields
        ]
        key = record_set.get(constants.SCHEMA_ORG_KEY)
        data = record_set.get(constants.ML_COMMONS_DATA)
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.decoder.JSONDecodeError:
                data = None
                issues.add_error(
                    f"{constants.ML_COMMONS_DATA} is not a proper list of JSON: {data}"
                )
        is_enumeration = record_set.get(constants.ML_COMMONS_IS_ENUMERATION)
        return cls(
            issues=issues,
            folder=folder,
            context=Context(
                dataset_name=context.dataset_name, record_set_name=record_set_name
            ),
            data=data,
            description=record_set.get(constants.SCHEMA_ORG_DESCRIPTION),
            is_enumeration=is_enumeration,
            key=key,
            fields=fields,
            name=record_set_name,
            rdf=rdf,
        )
