"""Metadata module."""

from __future__ import annotations

import dataclasses

from etils import epath

from mlcroissant._src.core import constants
from mlcroissant._src.core.data_types import check_expected_type
from mlcroissant._src.core.issues import Context
from mlcroissant._src.core.issues import Issues
from mlcroissant._src.core.issues import ValidationError
from mlcroissant._src.core.json_ld import expand_jsonld
from mlcroissant._src.core.json_ld import remove_empty_values
from mlcroissant._src.core.types import Json
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.graph import from_file_to_json
from mlcroissant._src.structure_graph.graph import from_nodes_to_graph
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.file_object import FileObject
from mlcroissant._src.structure_graph.nodes.file_set import FileSet
from mlcroissant._src.structure_graph.nodes.rdf import Rdf
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet
from mlcroissant._src.structure_graph.nodes.schema_org import Organization
from mlcroissant._src.structure_graph.nodes.schema_org import Person
from mlcroissant._src.structure_graph.nodes.schema_org import PropertyValue
from mlcroissant._src.structure_graph.nodes.schema_org import Thing


@dataclasses.dataclass(eq=False, repr=False)
class Metadata(Node):
    """Nodes to describe a dataset metadata."""

    # required
    description: str | None = None
    license: str | None = None
    name: str = ""
    url: str | None = ""
    distribution: list[FileObject | FileSet] = dataclasses.field(default_factory=list)
    record_sets: list[RecordSet] = dataclasses.field(default_factory=list)
    creator: list[Person | Organization] = dataclasses.field(default_factory=list)
    date_published: str | None = None
    # recommended
    keywords: list[str] = dataclasses.field(default_factory=list)
    publisher: list[Person | Organization] = dataclasses.field(default_factory=list)
    version: str | float | None = None
    date_created: str | None = None
    date_modified: str | None = None
    is_accessible_for_free: bool | None = None
    same_as: str | None = None  # URL
    # optional
    alternate_name: list[str] = dataclasses.field(default_factory=list)
    citation: list[str] = dataclasses.field(default_factory=list)
    is_based_on: list[str] = dataclasses.field(default_factory=list)  # URL's
    measurement_technique: str | None = None  # text / URL
    measurement_method: str | None = None  # text / URL
    variable_measured: str | None = None
    is_part_of: str | None = None  # URL
    maintainer: list[Organization | Person] = dataclasses.field(default_factory=list)
    included_in_data_catalog: list[str] = dataclasses.field(default_factory=list)  # URL
    issn: str | None = None

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
        self.assert_has_mandatory_properties(
            "name",
            "url",
            "distribution",
            "creator",
            "datePublished",
            "description",
            "license",
        )
        self.assert_has_optional_properties(
            "keywords",
            "publisher",
            "version",
            "dateCreated",
            "dateModified",
            "isAccessibleForFree",
            "sameAs",
        )

        # Raise exception if there are errors.
        for node in self.nodes():
            if node.issues.errors:
                raise ValidationError(node.issues.report())

    def to_json(self) -> Json:
        """Converts the `Metadata` to JSON."""

        return remove_empty_values(
            {
                "@context": self.rdf.context,
                "@type": "sc:Dataset",
                "name": self.name,
                "description": self.description,
                "license": self.license,
                "url": self.url,
                "creator": [p.to_json() for p in self.creator],
                "datePublished": self.date_published,
                "keywords": self.keywords,
                "publisher": [p.to_json() for p in self.publisher],
                "version": self.version,
                "dateCreated": self.date_created,
                "dateModified": self.date_modified,
                "isAccessibleForFree": self.is_accessible_for_free,
                "sameAs": self.same_as,
                "alternateName": self.alternate_name,
                "citation": self.citation,
                "isBasedOn": self.is_based_on,
                "measurementTechnique": self.measurement_technique,
                "measurementMethod": self.measurement_method,
                "variable_measured": self.variable_measured,
                "isPartOf": self.is_part_of,
                "maintainer": [p.to_json() for p in self.maintainer],
                "includedInDataCatalog": self.included_in_data_catalog,
                "issn": self.issn,
                "distribution": [f.to_json() for f in self.distribution],
                "recordSet": [record_set.to_json() for record_set in self.record_sets],
            }
        )

    @property
    def file_objects(self) -> list[FileObject]:
        """Gets `https://schema.org/FileObject` in the distribution."""
        return [
            file_object
            for file_object in self.distribution
            if isinstance(file_object, FileObject)
        ]

    @property
    def file_sets(self) -> list[FileSet]:
        """Gets `https://schema.org/FileSet` in the distribution."""
        return [
            file_set for file_set in self.distribution if isinstance(file_set, FileSet)
        ]

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
            field.data_type

    @classmethod
    def from_file(cls, issues: Issues, file: epath.PathLike) -> Metadata:
        """Creates the Metadata from a Croissant file."""
        folder, json_ = from_file_to_json(file)
        return cls.from_json(issues=issues, json_=json_, folder=folder)

    @classmethod
    def from_json(
        cls, issues: Issues, json_: Json, folder: epath.Path | None
    ) -> Metadata:
        """Creates a `Metadata` from JSON."""
        rdf = Rdf.from_json(json_)
        metadata = expand_jsonld(json_)
        return cls.from_jsonld(issues=issues, folder=folder, metadata=metadata, rdf=rdf)

    @classmethod
    def from_jsonld(
        cls,
        issues: Issues,
        folder: epath.Path | None,
        metadata: Json,
        rdf: Rdf | None = None,
    ) -> Metadata:
        """Creates a `Metadata` from JSON-LD."""
        if rdf is None:
            rdf = Rdf()
        check_expected_type(issues, metadata, constants.SCHEMA_ORG_DATASET)
        distribution: list[FileObject | FileSet] = []
        file_set_or_objects = metadata.get(constants.SCHEMA_ORG_DISTRIBUTION, [])
        dataset_name = metadata.get(constants.SCHEMA_ORG_NAME, "")
        context = Context(dataset_name=dataset_name)
        for set_or_object in file_set_or_objects:
            name = set_or_object.get(constants.SCHEMA_ORG_NAME, "")
            distribution_type = set_or_object.get("@type")
            if distribution_type == constants.SCHEMA_ORG_FILE_OBJECT:
                distribution.append(
                    FileObject.from_jsonld(issues, context, folder, rdf, set_or_object)
                )
            elif distribution_type == constants.SCHEMA_ORG_FILE_SET:
                distribution.append(
                    FileSet.from_jsonld(issues, context, folder, rdf, set_or_object)
                )
            else:
                issues.add_error(
                    f'"{name}" should have an attribute "@type":'
                    f' "{constants.SCHEMA_ORG_FILE_OBJECT}" or "@type":'
                    f' "{constants.SCHEMA_ORG_FILE_SET}". Got'
                    f" {distribution_type} instead."
                )
        record_sets = [
            RecordSet.from_jsonld(issues, context, folder, rdf, record_set)
            for record_set in metadata.get(constants.ML_COMMONS_RECORD_SET, [])
        ]
        url = metadata.get(constants.SCHEMA_ORG_URL)
        return cls(
            issues=issues,
            context=context,
            folder=folder,
            citation=metadata.get(constants.SCHEMA_ORG_CITATION),
            description=metadata.get(constants.SCHEMA_ORG_DESCRIPTION),
            distribution=distribution,
            license=metadata.get(constants.SCHEMA_ORG_LICENSE),
            name=dataset_name,
            record_sets=record_sets,
            url=url,
            rdf=rdf,
        )
