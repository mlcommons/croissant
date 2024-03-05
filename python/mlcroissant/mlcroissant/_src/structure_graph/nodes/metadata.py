"""Metadata module."""

from __future__ import annotations

import dataclasses
import datetime
import itertools
from typing import Any, Literal

from etils import epath
from rdflib import namespace
from rdflib.namespace import SDO
import requests

from mlcroissant._src.core import constants
from mlcroissant._src.core import dataclasses as mlc_dataclasses
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.core.dates import from_datetime_to_str
from mlcroissant._src.core.dates import from_str_to_datetime
from mlcroissant._src.core.issues import ValidationError
from mlcroissant._src.core.json_ld import expand_jsonld
from mlcroissant._src.core.json_ld import remove_empty_values
from mlcroissant._src.core.json_ld import unbox_singleton_list
from mlcroissant._src.core.rdf import Rdf
from mlcroissant._src.core.types import Json
from mlcroissant._src.core.url import is_url
from mlcroissant._src.structure_graph.base_node import NodeV2
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
    def from_jsonld(cls, ctx: Context, jsonld: Any) -> list[PersonOrOrganization]:
        """Builds the class from the JSON-LD."""
        if jsonld is None:
            return []
        elif isinstance(jsonld, list):
            persons_or_organizations: itertools.chain[PersonOrOrganization] = (
                itertools.chain.from_iterable([
                    cls.from_jsonld(ctx, element) for element in jsonld
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


def _distribution_from_jsonld(ctx: Context, jsonld: Json) -> list[FileObject | FileSet]:
    distribution: list[FileObject | FileSet] = []
    for set_or_object in jsonld:
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
    return distribution


def _distribution_to_json(ctx: Context, distribution: list[FileObject | FileSet]):
    return [resource.to_json() for resource in distribution]


def _date_from_jsonld(ctx: Context, jsonld: Json):
    return from_str_to_datetime(ctx.issues, jsonld)


def _date_to_jsonld(ctx: Context, date: datetime.datetime):
    del ctx
    return from_datetime_to_str(date)


@mlc_dataclasses.dataclass
class Metadata(NodeV2):
    """Nodes to describe a dataset metadata."""

    cite_as: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        description=(
            "A citation for a publication that describes the dataset. Ideally,"
            " citations should be expressed using the bibtex format. Note that this is"
            " different from schema.org/citation, which is used to make a citation to"
            " another publication from this dataset."
        ),
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_CITE_AS,
    )
    creators: list[PersonOrOrganization] | None = mlc_dataclasses.jsonld_field(
        cardinality="ONE",
        default_factory=list,
        description="The creator(s) of the dataset.",
        from_jsonld=PersonOrOrganization.from_jsonld,
        input_types=[PersonOrOrganization],
        to_jsonld=lambda ctx, person: PersonOrOrganization.to_json(person),
        url=constants.SCHEMA_ORG_CREATOR,
    )
    date_created: datetime.datetime | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="The date the dataset was initially created.",
        input_types=[SDO.Date, SDO.DateTime],
        url=constants.SCHEMA_ORG_DATE_CREATED,
    )
    date_modified: datetime.datetime | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="The date the dataset was last modified.",
        input_types=[SDO.Date, SDO.DateTime],
        url=constants.SCHEMA_ORG_DATE_MODIFIED,
    )
    date_published: datetime.datetime | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="The date the dataset was published.",
        input_types=[SDO.Date, SDO.DateTime],
        url=constants.SCHEMA_ORG_DATE_PUBLISHED,
    )
    description: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="Description of the dataset.",
        input_types=[SDO.Text],
        url=constants.SCHEMA_ORG_DESCRIPTION,
    )
    is_live_dataset: bool | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="Whether the dataset is a live dataset.",
        input_types=[SDO.Boolean],
        url=constants.ML_COMMONS_IS_LIVE_DATASET,
    )
    keywords: list[str] | None = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description=(
            "A set of keywords associated with the dataset, either as free text, or"
            " a DefinedTerm with a formal definition."
        ),
        input_types=[SDO.Text],
        url=constants.SCHEMA_ORG_KEYWORDS,
    )
    license: list[str] | None = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default=None,
        description=(
            "The license of the dataset. Croissant recommends using the URL of a"
            " known license, e.g., one of the licenses listed at"
            " https://spdx.org/licenses/."
        ),
        input_types=[SDO.URL],
        url=constants.SCHEMA_ORG_LICENSE,
    )
    name: str = mlc_dataclasses.jsonld_field(
        default="",
        description="The name of the dataset.",
        input_types=[SDO.Text],
        url=constants.SCHEMA_ORG_NAME,
    )
    publisher: list[PersonOrOrganization] | None = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description=(
            "The publisher of the dataset, which may be distinct from its creator."
        ),
        from_jsonld=PersonOrOrganization.from_jsonld,
        input_types=[PersonOrOrganization],
        to_jsonld=lambda ctx, person: PersonOrOrganization.to_json(person),
        url=constants.SCHEMA_ORG_PUBLISHER,
    )
    same_as: list[str] | None = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default_factory=list,
        description=(
            "The URL of another Web resource that represents the same dataset as this"
            " one."
        ),
        input_types=[SDO.URL],
        url=constants.SCHEMA_ORG_SAME_AS,
    )
    url: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        description=(
            "The URL of the dataset. This generally corresponds to the Web page for"
            " the dataset."
        ),
        input_types=[SDO.URL],
        url=constants.SCHEMA_ORG_URL,
    )
    # TODO: remove this default?
    version: str | None = mlc_dataclasses.jsonld_field(
        default="",
        description="The version of the dataset following the requirements below.",
        input_types=[SDO.Number, SDO.Text],
        url=constants.SCHEMA_ORG_VERSION,
    )
    distribution: list[FileObject | FileSet] = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default_factory=list,
        from_jsonld=_distribution_from_jsonld,
        input_types=[FileObject, FileSet],
        to_jsonld=_distribution_to_json,
        url=constants.SCHEMA_ORG_DISTRIBUTION,
    )
    record_sets: list[RecordSet] = mlc_dataclasses.jsonld_field(
        cardinality="MANY",
        default_factory=list,
        from_jsonld=lambda ctx, record_sets: [
            RecordSet.from_jsonld(ctx, record_set) for record_set in record_sets
        ],
        input_types=[RecordSet],
        to_jsonld=lambda ctx, record_sets: [
            record_set.to_json() for record_set in record_sets
        ],
        url=constants.ML_COMMONS_RECORD_SET,
    )
    data_collection: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_COLLECTION,
    )
    data_collection_type: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_COLLECTION_TYPE,
    )
    data_collection_type_others: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_COLLECTION_TYPE_OTHERS,
    )
    data_collection_missing: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_COLLECTION_MISSING,
    )
    data_collection_raw: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_COLLECTION_RAW,
    )
    data_collection_timeframe_start: datetime.datetime | None = (
        mlc_dataclasses.jsonld_field(
            default=None,
            from_jsonld=_date_from_jsonld,
            input_types=[SDO.Date, SDO.DateTime],
            to_jsonld=_date_to_jsonld,
            url=constants.ML_COMMONS_RAI_DATA_COLLECTION_TIMEFRAME_START,
        )
    )
    data_collection_timeframe_end: datetime.datetime | None = (
        mlc_dataclasses.jsonld_field(
            default=None,
            from_jsonld=_date_from_jsonld,
            input_types=[SDO.Date, SDO.DateTime],
            to_jsonld=_date_to_jsonld,
            url=constants.ML_COMMONS_RAI_DATA_COLLECTION_TIMEFRAME_END,
        )
    )
    data_preprocessing_imputation: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_PREPROCESSING_IMPUTATION,
    )
    data_preprocessing_protocol: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_PREPROCESSING_PROTOCOL,
    )
    data_preprocessing_manipulation: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_PREPROCESSING_MANIPULATION,
    )
    data_annotation_protocol: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_ANNOTATION_PROTOCOL,
    )
    data_annotation_platform: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_ANNOTATION_PLATFORM,
    )
    data_annotation_analysis: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_ANNOTATION_ANALYSIS,
    )
    data_annotation_peritem: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_ANNOTATION_PER_ITEM,
    )
    data_annotation_demographics: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_ANNOTATION_DEMOGRAPHICS,
    )
    data_annotation_tools: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_ANNOTATION_TOOLS,
    )
    data_biases: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_BIASES,
    )
    data_usecases: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_USE_CASES,
    )
    data_limitation: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_LIMITATION,
    )
    data_social_impact: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_SOCIAL_IMPACT,
    )
    data_sensitive: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_SENSITIVE,
    )
    data_maintenance: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        input_types=[SDO.Text],
        url=constants.ML_COMMONS_RAI_DATA_MAINTENANCE,
    )

    def __post_init__(self):
        """Checks arguments of the node and setup ID."""
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
        if self.ctx.is_v0():
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

    @classmethod
    def _JSONLD_TYPE(cls, ctx: Context):
        del ctx
        return constants.SCHEMA_ORG_DATASET

    def to_json(self) -> Json:
        """Converts the `Metadata` to JSON."""
        context = self.ctx.rdf.context
        if "@base" in context:
            if context["@base"] == constants.BASE_IRI:
                context.pop("@base")
        jsonld = super().to_json()
        jsonld.pop("@id", None)
        jsonld["@context"] = context
        conforms_to = self.ctx.conforms_to.to_json() if self.ctx.conforms_to else None
        jsonld["conformsTo"] = conforms_to
        return remove_empty_values(jsonld)

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

    def nodes(self) -> list[NodeV2]:
        """List all nodes in metadata."""
        nodes: list[NodeV2] = [self]
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
        jsonld = expand_jsonld(json_, ctx=ctx)
        return cls.from_jsonld(ctx=ctx, jsonld=jsonld)
