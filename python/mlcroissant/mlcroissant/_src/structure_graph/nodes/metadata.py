"""Metadata module."""

from __future__ import annotations

import dataclasses
import datetime
import itertools
from typing import Any, Literal

from etils import epath
from rdflib import namespace
import requests

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.core.data_types import check_expected_type
from mlcroissant._src.core.dates import from_datetime_to_str
from mlcroissant._src.core.dates import from_str_to_datetime
from mlcroissant._src.core.issues import ValidationError
from mlcroissant._src.core.json_ld import box_singleton_list
from mlcroissant._src.core.json_ld import expand_jsonld
from mlcroissant._src.core.json_ld import remove_empty_values
from mlcroissant._src.core.json_ld import unbox_singleton_list
from mlcroissant._src.core.rdf import Rdf
from mlcroissant._src.core.types import Json
from mlcroissant._src.core.url import is_url
from mlcroissant._src.core.uuid import generate_uuid
from mlcroissant._src.core.uuid import uuid_from_jsonld
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.graph import from_file_to_json
from mlcroissant._src.structure_graph.graph import from_nodes_to_graph
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.file_object import FileObject
from mlcroissant._src.structure_graph.nodes.file_set import FileSet
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet


@dataclasses.dataclass(eq=False, repr=False)
class PersonOrOrganization:
    """Representing either https://schema.org/Person or /Organization."""

    name: str | None = None
    description: str | None = None
    email: str | None = None
    type: (
        Literal["https://schema.org/Person", "https://schema.org/Organization"] | None
    ) = None
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
                    email=jsonld.get(constants.SCHEMA_ORG_EMAIL),
                    type=jsonld.get("@type"),
                    url=jsonld.get(constants.SCHEMA_ORG_URL),
                )
            ]

    @classmethod
    def to_json(cls, creator: list[PersonOrOrganization] | None) -> Any:
        """Serializes back to JSON-LD."""
        if creator is None:
            return None
        else:
            creators = [
                remove_empty_values({
                    "@type": (
                        "Person"
                        if element.type == namespace.SDO.Person
                        else "Organization"
                    ),
                    "email": element.email,
                    "name": element.name,
                    "description": element.description,
                    "url": element.url,
                })
                for element in creator
            ]
            return unbox_singleton_list(creators)


@dataclasses.dataclass(eq=False, repr=False)
class Metadata(Node):
    """Nodes to describe a dataset metadata."""

    uuid: dataclasses.InitVar[str]
    cite_as: str | None = None
    creators: list[PersonOrOrganization] | None = None
    date_created: datetime.datetime | None = None
    date_modified: datetime.datetime | None = None
    date_published: datetime.datetime | None = None
    description: str | None = None
    is_live_dataset: bool | None = None
    keywords: list[str] | None = None
    license: list[str] | None = None
    name: str = ""
    publisher: list[PersonOrOrganization] | None = None
    same_as: list[str] | None = None
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

    def __post_init__(self, uuid: str | None = None):
        """Checks arguments of the node."""
        del uuid
        self._uuid = generate_uuid()

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
        self.ctx.graph = from_nodes_to_graph(self)
        self.check_graph()

        # Check properties.
        self.validate_name()
        self.version = self.validate_version()
        self.license = self.validate_license()
        self.date_created = self.validate_date(self.date_created)
        self.date_modified = self.validate_date(self.date_modified)
        self.date_published = self.validate_date(self.date_published)
        self.assert_has_mandatory_properties("name")
        self.assert_has_optional_properties(
            "cite_as", "date_published", "license", "version"
        )

        # Raise exception if there are errors.
        for node in self.nodes():
            if node.ctx.issues.errors:
                raise ValidationError(node.ctx.issues.report())

        self.ctx.conforms_to = CroissantVersion.from_jsonld(
            self.ctx, self.ctx.conforms_to
        )

    def to_json(self) -> Json:
        """Converts the `Metadata` to JSON."""
        conforms_to = self.ctx.conforms_to.to_json() if self.ctx.conforms_to else None

        context = self.ctx.rdf.context
        if "@base" in context:
            if context["@base"] == constants.BASE_IRI:
                context.pop("@base")

        return remove_empty_values({
            "@context": context,
            "@type": "sc:Dataset",
            "name": self.name,
            "conformsTo": conforms_to,
            "description": self.description,
            "creator": PersonOrOrganization.to_json(self.creators),
            "dateCreated": from_datetime_to_str(self.date_created),
            "dateModified": from_datetime_to_str(self.date_modified),
            "datePublished": from_datetime_to_str(self.date_published),
            "dataBiases": self.data_biases,
            "dataCollection": self.data_collection,
            "citation": self.cite_as if self.ctx.is_v0() else None,
            "citeAs": None if self.ctx.is_v0() else self.cite_as,
            "isLiveDataset": self.is_live_dataset,
            "keywords": unbox_singleton_list(self.keywords),
            "license": unbox_singleton_list(self.license),
            "personalSensitiveInformation": self.personal_sensitive_information,
            "publisher": PersonOrOrganization.to_json(self.publisher),
            "url": self.url,
            "sameAs": unbox_singleton_list(self.same_as),
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

    def validate_version(self) -> str | None:
        """Validates the given version and returns a normalized string version.

        A valid version follows Semantic Versioning 2.0.0 `MAJOR.MINOR.PATCH`.
        For more information: https://semver.org/spec/v2.0.0.html.
        """
        version = self.version

        # Version is a recommended but not mandatory attribute.
        if version is None:
            return None

        if isinstance(version, str):
            numbers = version.split(".")
            are_not_all_numbers = any(not number.isnumeric() for number in numbers)
            if len(numbers) != 3 or are_not_all_numbers:
                self.add_warning(
                    f"Version doesn't follow MAJOR.MINOR.PATCH: {version}. For more"
                    " information refer to: https://semver.org/spec/v2.0.0.html"
                )
            return version
        elif isinstance(version, int):
            return f"{version}.0.0"
        elif isinstance(version, float):
            return f"{version}.0"
        else:
            self.add_error(
                f"The version should be a string or a number. Got: {type(version)}."
            )
            return None

    def validate_license(self) -> list[str] | None:
        """Validates the license as a list of strings."""
        license = self.license
        if license is None:
            return None
        elif isinstance(license, list):
            if any(not isinstance(el, str) for el in license):
                self.add_error(f"License should be a list of str. Got: {license}")
                return None
            return license
        elif isinstance(license, str):
            return [license]
        else:
            self.add_error(f"License should be a list of str. Got: {license}")
            return None

    def validate_date(self, date: Any) -> datetime.datetime | None:
        """Validates dates as a datetime for any input."""
        if date is None:
            return None
        elif isinstance(date, str):
            return from_str_to_datetime(self.ctx.issues, date)
        elif isinstance(date, datetime.datetime):
            return date
        elif isinstance(date, datetime.date):
            return datetime.datetime.combine(date, datetime.time.min)
        self.add_error(f"Wrong type for a date. Expected Date or Datetime. Got: {date}")
        return None

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
        if not self.ctx.graph.is_directed():
            self.ctx.issues.add_error("The structure graph is not directed.")
        fields = [node for node in self.ctx.graph.nodes if isinstance(node, Field)]
        # Check all fields have a data type: either on the field, on a parent.
        for field in fields:
            field.data_type

    @classmethod
    def from_file(cls, ctx: Context, file: epath.PathLike) -> Metadata:
        """Creates the Metadata from a Croissant file."""
        if is_url(file):
            response = requests.get(file)
            json_ = response.json()
            return cls.from_json(ctx=ctx, json_=json_)
        folder, json_ = from_file_to_json(file)
        ctx.folder = folder
        return cls.from_json(ctx=ctx, json_=json_)

    @classmethod
    def from_json(
        cls,
        ctx: Context,
        json_: Json,
    ) -> Metadata:
        """Creates a `Metadata` from JSON."""
        ctx.rdf = Rdf.from_json(ctx, json_)
        metadata = expand_jsonld(json_)
        return cls.from_jsonld(ctx=ctx, metadata=metadata)

    @classmethod
    def from_jsonld(cls, ctx: Context, metadata: Json) -> Metadata:
        """Creates a `Metadata` from JSON-LD."""
        check_expected_type(ctx.issues, metadata, constants.SCHEMA_ORG_DATASET)
        distribution: list[FileObject | FileSet] = []
        file_set_or_objects = metadata.get(constants.SCHEMA_ORG_DISTRIBUTION, [])
        dataset_name = metadata.get(constants.SCHEMA_ORG_NAME, "")
        ctx.conforms_to = CroissantVersion.from_jsonld(
            ctx, metadata.get(constants.DCTERMS_CONFORMS_TO)
        )

        if ctx.is_v0():
            cite_as = metadata.get(constants.SCHEMA_ORG_CITATION)
        else:
            cite_as = metadata.get(constants.ML_COMMONS_CITE_AS(ctx))

        for set_or_object in file_set_or_objects:
            name = set_or_object.get(constants.SCHEMA_ORG_NAME, "")
            distribution_type = set_or_object.get("@type")
            if distribution_type == constants.SCHEMA_ORG_FILE_OBJECT(ctx):
                distribution.append(FileObject.from_jsonld(ctx, set_or_object))
            elif distribution_type == constants.SCHEMA_ORG_FILE_SET(ctx):
                distribution.append(FileSet.from_jsonld(ctx, set_or_object))
            else:
                ctx.issues.add_error(
                    f'"{name}" should have an attribute "@type":'
                    f' "{constants.SCHEMA_ORG_FILE_OBJECT(ctx)}" or "@type":'
                    f' "{constants.SCHEMA_ORG_FILE_SET(ctx)}". Got'
                    f" {distribution_type} instead."
                )
        record_sets = [
            RecordSet.from_jsonld(ctx, record_set)
            for record_set in metadata.get(constants.ML_COMMONS_RECORD_SET(ctx), [])
        ]
        url = metadata.get(constants.SCHEMA_ORG_URL)
        creators = PersonOrOrganization.from_jsonld(
            metadata.get(constants.SCHEMA_ORG_CREATOR)
        )
        publisher = PersonOrOrganization.from_jsonld(
            metadata.get(constants.SCHEMA_ORG_PUBLISHER)
        )
        return cls(
            ctx=ctx,
            cite_as=cite_as,
            creators=creators,
            date_created=metadata.get(constants.SCHEMA_ORG_DATE_CREATED),
            date_modified=metadata.get(constants.SCHEMA_ORG_DATE_MODIFIED),
            date_published=metadata.get(constants.SCHEMA_ORG_DATE_PUBLISHED),
            description=metadata.get(constants.SCHEMA_ORG_DESCRIPTION),
            data_biases=metadata.get(constants.ML_COMMONS_DATA_BIASES(ctx)),
            data_collection=metadata.get(constants.ML_COMMONS_DATA_COLLECTION(ctx)),
            distribution=distribution,
            is_live_dataset=metadata.get(constants.ML_COMMONS_IS_LIVE_DATASET(ctx)),
            keywords=metadata.get(constants.SCHEMA_ORG_KEYWORDS),
            license=metadata.get(constants.SCHEMA_ORG_LICENSE),
            name=dataset_name,
            personal_sensitive_information=metadata.get(
                constants.ML_COMMONS_PERSONAL_SENSITVE_INFORMATION(ctx)
            ),
            publisher=publisher,
            record_sets=record_sets,
            same_as=box_singleton_list(metadata.get(constants.SCHEMA_ORG_SAME_AS)),
            uuid=uuid_from_jsonld(metadata),
            url=url,
            version=metadata.get(constants.SCHEMA_ORG_VERSION),
        )
