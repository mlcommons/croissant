"""Metadata module."""

from __future__ import annotations

import dataclasses
import json

from etils import epath

from ml_croissant._src.core import constants
from ml_croissant._src.core.data_types import check_expected_type
from ml_croissant._src.core.issues import Context
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.core.issues import ValidationError
from ml_croissant._src.core.json_ld import _make_context
from ml_croissant._src.core.json_ld import expand_jsonld
from ml_croissant._src.core.json_ld import from_jsonld_to_json
from ml_croissant._src.core.json_ld import remove_empty_values
from ml_croissant._src.core.types import Json
from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.graph import from_file_to_jsonld
from ml_croissant._src.structure_graph.graph import from_nodes_to_graph
from ml_croissant._src.structure_graph.nodes.field import Field
from ml_croissant._src.structure_graph.nodes.file_object import FileObject
from ml_croissant._src.structure_graph.nodes.file_set import FileSet
from ml_croissant._src.structure_graph.nodes.record_set import RecordSet


@dataclasses.dataclass(eq=False, repr=False)
class Metadata(Node):
    """Nodes to describe a dataset metadata."""

    citation: str | None = None
    description: str | None = None
    language: str | None = None
    license: str | None = None
    name: str = ""
    url: str = ""
    file_objects: list[FileObject] = dataclasses.field(default_factory=list)
    file_sets: list[FileSet] = dataclasses.field(default_factory=list)
    record_sets: list[RecordSet] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        """Checks arguments of the node."""
        # Define parents.
        for node in self.distribution:
            node.parents = [self]
        for record_set in self.record_sets:
            record_set.parents = [self]
            for field in record_set.fields:
                field.parents = [self, record_set]
                for sub_field in field.sub_fields:
                    sub_field.parents = [self, record_set, field]

        # Back-fill the graph in every node.
        self.graph = from_nodes_to_graph(self)
        self.check_graph()

        # Check properties.
        self.validate_name()
        self.assert_has_mandatory_properties("name", "url")
        self.assert_has_optional_properties("citation", "license")

        # Raise exception if there are errors.
        for node in self.nodes():
            if node.issues.errors:
                raise ValidationError(node.issues.report())

    def to_json(self) -> Json:
        """Converts the `Metadata` to JSON."""
        return remove_empty_values(
            {
                "@context": _make_context(),
                "@language": self.language,
                "@type": "sc:Dataset",
                "name": self.name,
                "description": self.description,
                "citation": self.citation,
                "license": self.license,
                "url": self.url,
                "distribution": [f.to_json() for f in self.distribution],
                "recordSet": [record_set.to_json() for record_set in self.record_sets],
            }
        )

    @property
    def distribution(self) -> list[FileObject | FileSet]:
        """Gets `https://schema.org/distribution`: union of FileSets and FileObjects."""
        return self.file_objects + self.file_sets

    def nodes(self) -> list[Node]:
        """List all nodes in metadata."""
        nodes: list[Node] = [self]
        nodes.extend(self.distribution)
        nodes.extend(self.record_sets)
        for record_set in self.record_sets:
            nodes.extend(record_set.fields)
            for field in record_set.fields:
                nodes.extend(field.sub_fields)
        return nodes

    def check_graph(self):
        """Checks the integrity of the structure graph.

        The rules are the following:
        - The graph is directed.
        - All fields have a data type: either directly specified, or on a parent.

        Args:
            issues: The issues to populate in case of problem.
            graph: The structure graph to be checked.
        """
        # Check that the graph is directed.
        if not self.graph.is_directed():
            self.issues.add_error("The structure graph is not directed.")
        fields = [node for node in self.graph.nodes if isinstance(node, Field)]
        # Check all fields have a data type: either on the field, on a parent.
        for field in fields:
            field.actual_data_type

    @classmethod
    def from_file(cls, issues: Issues, file: epath.PathLike) -> Metadata:
        """Creates the Metadata from a Croissant file."""
        folder, jsonld = from_file_to_jsonld(file)
        json_ = from_jsonld_to_json(jsonld)
        return cls.from_json(issues=issues, json_=json_, folder=folder)

    @classmethod
    def from_json(
        cls, issues: Issues, json_: str | Json, folder: epath.Path | None
    ) -> Metadata:
        """Creates a `Metadata` from JSON."""
        if isinstance(json_, str):
            json_ = json.loads(json_)
        metadata = expand_jsonld(json_)
        return cls.from_jsonld(issues=issues, folder=folder, metadata=metadata)

    @classmethod
    def from_jsonld(
        cls,
        issues: Issues,
        folder: epath.Path | None,
        metadata: Json,
    ) -> Metadata:
        """Creates a `Metadata` from JSON-LD."""
        check_expected_type(issues, metadata, constants.SCHEMA_ORG_DATASET)
        file_sets: list[FileSet] = []
        file_objects: list[FileObject] = []
        record_sets: list[RecordSet] = []
        distributions = metadata.get(constants.SCHEMA_ORG_DISTRIBUTION, [])
        dataset_name = metadata.get(constants.SCHEMA_ORG_NAME, "")
        context = Context(dataset_name=dataset_name)
        for distribution in distributions:
            name = distribution.get(constants.SCHEMA_ORG_NAME, "")
            distribution_type = distribution.get("@type")
            if distribution_type == constants.SCHEMA_ORG_FILE_OBJECT:
                file_objects.append(
                    FileObject.from_jsonld(issues, context, folder, distribution)
                )
            elif distribution_type == constants.SCHEMA_ORG_FILE_SET:
                file_sets.append(
                    FileSet.from_jsonld(issues, context, folder, distribution)
                )
            else:
                issues.add_error(
                    f'"{name}" should have an attribute "@type":'
                    f' "{constants.SCHEMA_ORG_FILE_OBJECT}" or "@type":'
                    f' "{constants.SCHEMA_ORG_FILE_SET}". Got'
                    f" {distribution_type} instead."
                )
        record_sets = metadata.get(constants.ML_COMMONS_RECORD_SET, [])
        record_sets = [
            RecordSet.from_jsonld(issues, context, folder, record_set)
            for record_set in record_sets
        ]
        return cls(
            issues=issues,
            context=context,
            folder=folder,
            citation=metadata.get(constants.SCHEMA_ORG_CITATION),
            description=metadata.get(constants.SCHEMA_ORG_DESCRIPTION),
            file_objects=file_objects,
            file_sets=file_sets,
            language=metadata.get(constants.SCHEMA_ORG_LANGUAGE),
            license=metadata.get(constants.SCHEMA_ORG_LICENSE),
            name=dataset_name,
            record_sets=record_sets,
            url=metadata.get(constants.SCHEMA_ORG_URL),
        )
