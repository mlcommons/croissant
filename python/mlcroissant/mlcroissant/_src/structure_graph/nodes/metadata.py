"""Metadata module."""

from __future__ import annotations

import dataclasses
import datetime
import itertools
from typing import Any

from etils import epath

from mlcroissant._src.core import constants
from mlcroissant._src.core.data_types import check_expected_type
from mlcroissant._src.core.dates import from_str_to_date_time
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


@dataclasses.dataclass(eq=False, repr=False)
class PersonOrOrganization:
    """Representing either https://schema.org/Person or /Organization."""

    name: str | None = None
    description: str | None = None
    url: str | None = None

    @classmethod
    def from_jsonld(cls, jsonld: Any) -> list[PersonOrOrganization]:
        """Builds the class from the JSON-LD."""
        if jsonld is None:
            return []
        elif isinstance(jsonld, list):
            persons_or_organizations: itertools.chain[PersonOrOrganization] = (
                itertools.chain.from_iterable([
                    cls.from_jsonld(element) for element in jsonld
                ])
            )
            return list(persons_or_organizations)
        else:
            return [
                cls(
                    name=jsonld.get(constants.SCHEMA_ORG_NAME),
                    description=jsonld.get(constants.SCHEMA_ORG_DESCRIPTION),
                    url=jsonld.get(constants.SCHEMA_ORG_URL),
                )
            ]

    def to_json(self) -> Json:
        """Serializes back to JSON-LD."""
        return remove_empty_values({
            "name": self.name,
            "description": self.description,
            "url": self.url,
        })


@dataclasses.dataclass(eq=False, repr=False)
class Metadata(Node):
    """Nodes to describe a dataset metadata."""

    conforms_to: str | None = None
    citation: str | None = None
    creators: list[PersonOrOrganization] = dataclasses.field(default_factory=list)
    date_published: datetime.datetime | None = None
    description: str | None = None
    license: str | None = None
    name: str = ""
    url: str | None = ""
    version: str | None = ""
    distribution: list[FileObject | FileSet] = dataclasses.field(default_factory=list)
    record_sets: list[RecordSet] = dataclasses.field(default_factory=list)
    # RAI field - Involves understanding the potential risks associated with data usage
    # and to prevent unintended and potentially harmful consequences that may arise from
    # using models trained on or evaluated with the respective data.
    data_biases: str | None = None
    # RAI field - Key stages of the data collection process encourage its creators to
    # reflect on the process and improves understanding for users.
    data_collection: str | None = None
    # RAI field - Personal and sensitive information, if contained within the dataset,
    # can play an important role in the mitigation of any risks and the responsible use
    # of the datasets.
    personal_sensitive_information: str | None = None

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
        self.validate_version()
        self.assert_has_mandatory_properties("name")
        self.assert_has_optional_properties("citation", "license", "version")

        # Raise exception if there are errors.
        for node in self.nodes():
            if node.issues.errors:
                raise ValidationError(node.issues.report())

    def to_json(self) -> Json:
        """Converts the `Metadata` to JSON."""
        date_published = (
            self.date_published.isoformat() if self.date_published else None
        )
        creator: Json | list[Json] | None
        if len(self.creators) == 1:
            creator = self.creators[0].to_json()
        elif len(self.creators) > 1:
            creator = [creator.to_json() for creator in self.creators]
        else:
            creator = None
        return remove_empty_values({
            "@context": self.rdf.context,
            "@type": "sc:Dataset",
            "name": self.name,
            "conformsTo": self.conforms_to,
            "description": self.description,
            "creator": creator,
            "datePublished": date_published,
            "dataBiases": self.data_biases,
            "dataCollection": self.data_collection,
            "citation": self.citation,
            "license": self.license,
            "personalSensitiveInformation": self.personal_sensitive_information,
            "url": self.url,
            "version": self.version,
            "distribution": [f.to_json() for f in self.distribution],
            "recordSet": [record_set.to_json() for record_set in self.record_sets],
        })

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

    def validate_version(self) -> None:
        """Validates the given version.

        A valid version follows Semantic Versioning 2.0.0 `MAJOR.MINOR.PATCH`.
        For more information: https://semver.org/spec/v2.0.0.html.
        """
        version = self.version

        # Version is a recommended but not mandatory attribute.
        if not version:
            return

        if isinstance(version, str):
            points = version.count(".")
            numbers = version.replace(".", "")
            if points != 2 or len(numbers) != 3 or not numbers.isnumeric():
                self.add_error(
                    f"Version doesn't follow MAJOR.MINOR.PATCH: {version}. For more"
                    " information refer to: https://semver.org/spec/v2.0.0.html"
                )
        else:
            self.add_error(f"The version should be a string. Got: {type(version)}.")
            return

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
        creators = PersonOrOrganization.from_jsonld(
            metadata.get(constants.SCHEMA_ORG_CREATOR)
        )
        date_published = from_str_to_date_time(
            issues, metadata.get(constants.SCHEMA_ORG_DATE_PUBLISHED)
        )
        return cls(
            issues=issues,
            context=context,
            folder=folder,
            conforms_to=metadata.get(constants.DCTERMS_CONFORMS_TO),
            citation=metadata.get(constants.SCHEMA_ORG_CITATION),
            creators=creators,
            date_published=date_published,
            description=metadata.get(constants.SCHEMA_ORG_DESCRIPTION),
            data_biases=metadata.get(constants.ML_COMMONS_DATA_BIASES),
            data_collection=metadata.get(constants.ML_COMMONS_DATA_COLLECTION),
            distribution=distribution,
            license=metadata.get(constants.SCHEMA_ORG_LICENSE),
            name=dataset_name,
            personal_sensitive_information=metadata.get(
                constants.ML_COMMONS_PERSONAL_SENSITVE_INFORMATION
            ),
            record_sets=record_sets,
            url=url,
            version=metadata.get(constants.SCHEMA_ORG_VERSION),
            rdf=rdf,
        )
