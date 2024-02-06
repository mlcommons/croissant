"""Metadata module."""

from __future__ import annotations

import dataclasses
import datetime
import itertools
from typing import Any

from etils import epath
import requests

from mlcroissant._src.core import constants
from mlcroissant._src.core.context import Context
from mlcroissant._src.core.context import CroissantVersion
from mlcroissant._src.core.data_types import check_expected_type
from mlcroissant._src.core.dates import from_str_to_date_time
from mlcroissant._src.core.issues import ValidationError
from mlcroissant._src.core.json_ld import expand_jsonld
from mlcroissant._src.core.json_ld import remove_empty_values
from mlcroissant._src.core.rdf import Rdf
from mlcroissant._src.core.types import Json
from mlcroissant._src.core.url import is_url
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
    url: str | None = None

    @classmethod
    def from_jsonld(cls, jsonld: Any) -> list[PersonOrOrganization]:
        """Builds the class from the JSON-LD."""
        if jsonld is None:
            return []
        elif isinstance(jsonld, list):
            persons_or_organizations: itertools.chain[
                PersonOrOrganization
            ] = itertools.chain.from_iterable(
                [cls.from_jsonld(element) for element in jsonld]
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
        return remove_empty_values(
            {
                "name": self.name,
                "description": self.description,
                "url": self.url,
            }
        )


@dataclasses.dataclass(eq=False, repr=False)
class Metadata(Node):
    """Nodes to describe a dataset metadata."""

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
    #  RAI extension attributes
    data_collection: str | None = None
    data_collection_type: str | None = None
    data_collection_type_others: str | None = None
    data_collection_missing: str | None = None
    data_collection_raw: str | None = None
    data_collection_timeframe_start: datetime.datetime | None = None
    data_collection_timeframe_end: datetime.datetime | None = None
    data_preprocessing_imputation: str | None = None
    data_preprocessing_protocol: str | None = None
    data_preprocessing_manipulation: str | None = None
    data_annotation_protocol: str | None = None
    data_annotation_platform: str | None = None
    data_annotation_analysis: str | None = None
    data_annotation_peritem: str | None = None
    data_annotation_demographics: str | None = None
    data_annotation_tools: str | None = None
    data_biases: str | None = None
    data_usecases: str | None = None
    data_limitation: str | None = None
    data_social_impact: str | None = None
    data_sensitive: str | None = None
    data_maintenance: str | None = None
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
        self.ctx.graph = from_nodes_to_graph(self)
        self.check_graph()

        # Check properties.
        self.validate_name()
        self.validate_version()
        self.assert_has_mandatory_properties("name")
        self.assert_has_optional_properties("citation", "license", "version")

        # Raise exception if there are errors.
        for node in self.nodes():
            if node.ctx.issues.errors:
                raise ValidationError(node.ctx.issues.report())

        self.ctx.conforms_to = CroissantVersion.from_jsonld(
            self.ctx, self.ctx.conforms_to
        )

    def to_json(self) -> Json:
        """Converts the `Metadata` to JSON."""
        date_published = (
            self.date_published.isoformat() if self.date_published else None
        )
        data_collection_timeframe_start = (
            self.data_collection_timeframe_start.isoformat()
            if self.data_collection_timeframe_start
            else None
        )
        data_collection_timeframe_end = (
            self.data_collection_timeframe_end.isoformat()
            if self.data_collection_timeframe_end
            else None
        )
        creator: Json | list[Json] | None
        if len(self.creators) == 1:
            creator = self.creators[0].to_json()
        elif len(self.creators) > 1:
            creator = [creator.to_json() for creator in self.creators]
        else:
            creator = None
        conforms_to = self.ctx.conforms_to.to_json() if self.ctx.conforms_to else None
        return remove_empty_values(
            {
                "@context": self.ctx.rdf.context,
                "@type": "sc:Dataset",
                "name": self.name,
                "conformsTo": conforms_to,
                "description": self.description,
                "creator": creator,
                "datePublished": date_published,
                #  RAI extension
                "dataCollection": self.data_collection,
                "dataCollectionType": self.data_collection_type,
                "dataCollectionTypeOthers": self.data_collection_type_others,
                "dataCollectionMissing": self.data_collection_missing,
                "dataCollectionRaw": self.data_collection_raw,
                "dataCollectionTimeFrameStart": data_collection_timeframe_start,
                "dataCollectionTimeFrameEnd": data_collection_timeframe_end,
                "dataPreprocessingImputation": self.data_preprocessing_imputation,
                "dataPreprocessingProtocol": self.data_preprocessing_protocol,
                "dataPreprocessingManipulation": self.data_preprocessing_manipulation,
                "dataAnnotationProtocol": self.data_annotation_protocol,
                "dataAnnotationPlatform": self.data_annotation_platform,
                "dataAnnotationAnalysis": self.data_annotation_analysis,
                "dataAnnotationPerItem": self.data_annotation_peritem,
                "dataAnnotationDemographics": self.data_annotation_demographics,
                "dataAnnotationTools": self.data_annotation_tools,
                "dataBiases": self.data_biases,
                "dataUseCases": self.data_usecases,
                "dataLimitations": self.data_limitation,
                "dataSocialImpact": self.data_social_impact,
                "dataSensitive": self.data_sensitive,
                "dataMaitenance": self.data_maintenance,
                "citation": self.citation,
                "license": self.license,
                "personalSensitiveInformation": self.personal_sensitive_information,
                "url": self.url,
                "version": self.version,
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
        date_published = from_str_to_date_time(
            ctx.issues, metadata.get(constants.SCHEMA_ORG_DATE_PUBLISHED)
        )
        date_collection_timeframe_start = from_str_to_date_time(
            ctx.issues,
            metadata.get(constants.ML_COMMONS_RAI_DATA_COLLECTION_TIMEFRAME_START(ctx)),
        )
        date_collection_timeframe_end = from_str_to_date_time(
            ctx.issues,
            metadata.get(constants.ML_COMMONS_RAI_DATA_COLLECTION_TIMEFRAME_END(ctx)),
        )
        return cls(
            ctx=ctx,
            citation=metadata.get(constants.SCHEMA_ORG_CITATION),
            creators=creators,
            date_published=date_published,
            description=metadata.get(constants.SCHEMA_ORG_DESCRIPTION),
            data_collection=metadata.get(constants.ML_COMMONS_RAI_DATA_COLLECTION(ctx)),
            data_collection_type=metadata.get(
                constants.ML_COMMONS_RAI_DATA_COLLECTION_TYPE(ctx)
            ),
            data_collection_type_others=metadata.get(
                constants.ML_COMMONS_RAI_DATA_COLLECTION_TYPE_OTHERS(ctx)
            ),
            data_collection_missing=metadata.get(
                constants.ML_COMMONS_RAI_DATA_COLLECTION_MISSING(ctx)
            ),
            data_collection_raw=metadata.get(
                constants.ML_COMMONS_RAI_DATA_COLLECTION_RAW_DATA(ctx)
            ),
            data_collection_timeframe_start=date_collection_timeframe_start,
            data_collection_timeframe_end=date_collection_timeframe_end,
            data_preprocessing_imputation=metadata.get(
                constants.ML_COMMONS_RAI_DATA_PREPROCESSING_IMPUTATION(ctx)
            ),
            data_preprocessing_protocol=metadata.get(
                constants.ML_COMMONS_RAI_DATA_PREPROCESSING_PROTOCOL(ctx)
            ),
            data_preprocessing_manipulation=metadata.get(
                constants.ML_COMMONS_RAI_DATA_PREPROCESSING_MANIPULATION(ctx)
            ),
            data_annotation_protocol=metadata.get(
                constants.ML_COMMONS_RAI_DATA_ANNOTATION_PROTOCOL(ctx)
            ),
            data_annotation_platform=metadata.get(
                constants.ML_COMMONS_RAI_DATA_ANNOTATION_PLATFORM(ctx)
            ),
            data_annotation_analysis=metadata.get(
                constants.ML_COMMONS_RAI_DATA_ANNOTATION_ANALYSIS(ctx)
            ),
            data_annotation_peritem=metadata.get(
                constants.ML_COMMONS_RAI_DATA_ANNOTATION_PERITEM(ctx)
            ),
            data_annotation_demographics=metadata.get(
                constants.ML_COMMONS_RAI_DATA_ANNOTATION_DEMOGRAPHICS(ctx)
            ),
            data_annotation_tools=metadata.get(
                constants.ML_COMMONS_RAI_DATA_ANNOTATION_TOOLS(ctx)
            ),
            data_biases=metadata.get(constants.ML_COMMONS_RAI_DATA_BIAS(ctx)),
            data_usecases=metadata.get(constants.ML_COMMONS_RAI_DATA_USECASES(ctx)),
            data_limitation=metadata.get(constants.ML_COMMONS_RAI_DATA_LIMITATION(ctx)),
            data_social_impact=metadata.get(
                constants.ML_COMMONS_RAI_DATA_SOCIAL_IMPACT(ctx)
            ),
            data_sensitive=metadata.get(constants.ML_COMMONS_RAI_DATA_SENSITIVE(ctx)),
            data_maintenance=metadata.get(
                constants.ML_COMMONS_RAI_DATA_MAINTENANCE(ctx)
            ),
            distribution=distribution,
            license=metadata.get(constants.SCHEMA_ORG_LICENSE),
            name=dataset_name,
            personal_sensitive_information=metadata.get(
                constants.ML_COMMONS_PERSONAL_SENSITVE_INFORMATION(ctx)
            ),
            record_sets=record_sets,
            url=url,
            version=metadata.get(constants.SCHEMA_ORG_VERSION),
        )
