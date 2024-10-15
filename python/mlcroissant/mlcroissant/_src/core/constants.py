"""constants module."""

# flake8: noqa

import os

from etils import epath
import rdflib
from rdflib import namespace
from rdflib import term

# MLCommons-defined URIs.
ML_COMMONS_V_0_8 = rdflib.Namespace("http://mlcommons.org/schema/")
ML_COMMONS_V_1_0 = rdflib.Namespace("http://mlcommons.org/croissant/")


# Value for the base IRI used when expanding @ids in the JSON-LD.
BASE_IRI = "cr_base_iri/"


# ctx: Context is untyped to avoid cyclic dependencies. A unit test tests the behaviour.
def ML_COMMONS(ctx) -> rdflib.Namespace:
    """Switches the main Croissant namespace according to the version."""
    if ctx.is_v0():  # pytype: disable=attribute-error
        return ML_COMMONS_V_0_8
    else:
        return ML_COMMONS_V_1_0


ML_COMMONS_CITE_AS = lambda ctx: (
    SCHEMA_ORG_CITATION if ctx.is_v0() else ML_COMMONS(ctx).citeAs
)
ML_COMMONS_COLUMN = lambda ctx: ML_COMMONS(ctx).column
ML_COMMONS_DATA = lambda ctx: ML_COMMONS(ctx).data
ML_COMMONS_DATA_BIASES = lambda ctx: ML_COMMONS(ctx).dataBiases
ML_COMMONS_DATA_COLLECTION = lambda ctx: ML_COMMONS(ctx).dataCollection
ML_COMMONS_DATA_TYPE = lambda ctx: ML_COMMONS(ctx).dataType
ML_COMMONS_DATA_TYPE_BOUNDING_BOX = lambda ctx: ML_COMMONS(ctx).BoundingBox
ML_COMMONS_EQUIVALENT_PROPERTY = lambda ctx: ML_COMMONS(ctx).equivalentProperty
ML_COMMONS_EXAMPLES = lambda ctx: ML_COMMONS(ctx).examples
ML_COMMONS_EXCLUDES = lambda ctx: ML_COMMONS(ctx).excludes
ML_COMMONS_EXTRACT = lambda ctx: ML_COMMONS(ctx).extract
ML_COMMONS_FILE_PROPERTY = lambda ctx: ML_COMMONS(ctx).fileProperty
ML_COMMONS_FIELD = lambda ctx: ML_COMMONS(ctx).field
ML_COMMONS_FIELD_TYPE = lambda ctx: ML_COMMONS(ctx).Field
ML_COMMONS_FILE_OBJECT = lambda ctx: ML_COMMONS(ctx).fileObject
ML_COMMONS_FILE_SET = lambda ctx: ML_COMMONS(ctx).fileSet
# ML_COMMONS.format is understood as the `format` method on the class Namespace.
ML_COMMONS_FORMAT = lambda ctx: ML_COMMONS(ctx)["format"]
ML_COMMONS_INCLUDES = lambda ctx: ML_COMMONS(ctx).includes
ML_COMMONS_IS_ENUMERATION = lambda ctx: ML_COMMONS(ctx).isEnumeration
ML_COMMONS_IS_LIVE_DATASET = lambda ctx: ML_COMMONS(ctx).isLiveDataset
ML_COMMONS_JSON_PATH = lambda ctx: ML_COMMONS(ctx).jsonPath
ML_COMMONS_PARENT_FIELD = lambda ctx: ML_COMMONS(ctx).parentField
ML_COMMONS_PATH = lambda ctx: ML_COMMONS(ctx).path
ML_COMMONS_PERSONAL_SENSITVE_INFORMATION = lambda ctx: ML_COMMONS(
    ctx
).personalSensitiveInformation
ML_COMMONS_RECORD_SET = lambda ctx: ML_COMMONS(ctx).recordSet
ML_COMMONS_RECORD_SET_TYPE = lambda ctx: ML_COMMONS(ctx).RecordSet
ML_COMMONS_REFERENCES = lambda ctx: ML_COMMONS(ctx).references
ML_COMMONS_REGEX = lambda ctx: ML_COMMONS(ctx).regex
ML_COMMONS_REPEATED = lambda ctx: ML_COMMONS(ctx).repeated
# ML_COMMONS.replace is understood as the `replace` method on the class Namespace.
ML_COMMONS_REPLACE = lambda ctx: ML_COMMONS(ctx)["replace"]
ML_COMMONS_SEPARATOR = lambda ctx: ML_COMMONS(ctx).separator
ML_COMMONS_SOURCE = lambda ctx: ML_COMMONS(ctx).source
ML_COMMONS_SUB_FIELD = lambda ctx: ML_COMMONS(ctx).subField
ML_COMMONS_SUB_FIELD_TYPE = lambda ctx: ML_COMMONS(ctx).SubField
ML_COMMONS_TRANSFORM = lambda ctx: ML_COMMONS(ctx).transform

# Croissant RAI extension
# V1.0 namespace
RAI = rdflib.Namespace("http://mlcommons.org/croissant/RAI/")
# Attributes
ML_COMMONS_RAI_DATA_COLLECTION = RAI.dataCollection
ML_COMMONS_RAI_DATA_COLLECTION_TYPE = RAI.dataCollectionType
ML_COMMONS_RAI_DATA_COLLECTION_MISSING_DATA = RAI.dataCollectionMissingData
ML_COMMONS_RAI_DATA_COLLECTION_RAW_DATA = RAI.dataCollectionRawData
ML_COMMONS_RAI_DATA_COLLECTION_TIME_FRAME = RAI.dataCollectionTimeFrame
ML_COMMONS_RAI_DATA_IMPUTATION_PROTOCOL = RAI.dataImputationProtocol
ML_COMMONS_RAI_DATA_PREPROCESSING_PROTOCOL = RAI.dataPreprocessingProtocol
ML_COMMONS_RAI_DATA_DATA_MANIPULATION_PROTOCOL = RAI.dataDataManipulationProtocol
ML_COMMONS_RAI_DATA_ANNOTATION_PROTOCOL = RAI.dataAnnotationProtocol
ML_COMMONS_RAI_DATA_ANNOTATION_PLATFORM = RAI.dataAnnotationPlatform
ML_COMMONS_RAI_DATA_ANNOTATION_ANALYSIS = RAI.dataAnnotationAnalysis
ML_COMMONS_RAI_ANNOTATIONS_PER_ITEM = RAI.annotationsPerItem
ML_COMMONS_RAI_ANNOTATOR_DEMOGRAPHICS = RAI.annotatorDemographics
ML_COMMONS_RAI_MACHINE_ANNOTATION_TOOLS = RAI.machineAnnotationTools
ML_COMMONS_RAI_DATA_USE_CASES = RAI.dataUseCases
ML_COMMONS_RAI_DATA_BIASES = RAI.dataBiases
ML_COMMONS_RAI_DATA_LIMITATIONS = RAI.dataLimitations
ML_COMMONS_RAI_DATA_SOCIAL_IMPACT = RAI.dataSocialImpact
ML_COMMONS_RAI_PERSONAL_SENSITIVE_INFORMATION = RAI.personalSensitiveInformation
ML_COMMONS_RAI_DATA_RELEASE_MAINTENANCE_PLAN = RAI.dataReleaseMaintenancePlan

# RDF standard URIs.
# For "@type" key:
RDF_TYPE = namespace.RDF.type

# Dublin Core terms standard URIs.
DCTERMS = "http://purl.org/dc/terms/"
DCTERMS_CONFORMS_TO = namespace.DCTERMS.conformsTo

# Wikidata standard URIs.
WIKIDATA = rdflib.Namespace("https://www.wikidata.org/wiki/")

# Schema.org standard URIs.
SCHEMA_ORG_CITATION: term.URIRef = namespace.SDO.citation
SCHEMA_ORG_CONTAINED_IN = namespace.SDO.containedIn
SCHEMA_ORG_CONTENT_SIZE = namespace.SDO.contentSize
SCHEMA_ORG_CONTENT_URL = namespace.SDO.contentUrl
SCHEMA_ORG_CREATOR = namespace.SDO.creator
SCHEMA_ORG_DATE_CREATED = namespace.SDO.dateCreated
SCHEMA_ORG_DATE_MODIFIED = namespace.SDO.dateModified
SCHEMA_ORG_DATE_PUBLISHED = namespace.SDO.datePublished
SCHEMA_ORG_DATASET = namespace.SDO.Dataset
SCHEMA_ORG_DATA_TYPE_AUDIO_OBJECT = namespace.SDO.AudioObject
SCHEMA_ORG_DATA_TYPE_BOOL = namespace.SDO.Boolean
SCHEMA_ORG_DATA_TYPE_DATE = namespace.SDO.Date
SCHEMA_ORG_DATA_TYPE_FLOAT = namespace.SDO.Float
SCHEMA_ORG_DATA_TYPE_IMAGE_OBJECT = namespace.SDO.ImageObject
SCHEMA_ORG_DATA_TYPE_INTEGER = namespace.SDO.Integer
SCHEMA_ORG_DATA_TYPE_TEXT = namespace.SDO.Text
SCHEMA_ORG_DATA_TYPE_URL = namespace.SDO.URL
SCHEMA_ORG_DESCRIPTION = namespace.SDO.description
SCHEMA_ORG_DISTRIBUTION = namespace.SDO.distribution
SCHEMA_ORG_EMAIL = namespace.SDO.email
SCHEMA_ORG_ENCODING_FORMAT = namespace.SDO.encodingFormat
SCHEMA_ORG_KEYWORDS = namespace.SDO.keywords
SCHEMA_ORG_LICENSE = namespace.SDO.license
SCHEMA_ORG_NAME = namespace.SDO.name
SCHEMA_ORG_PUBLISHER = namespace.SDO.publisher
SCHEMA_ORG_SAME_AS = namespace.SDO.sameAs
SCHEMA_ORG_SHA256 = namespace.SDO.sha256
SCHEMA_ORG_URL = namespace.SDO.url
SCHEMA_ORG_VERSION = namespace.SDO.version

# Schema.org URIs that do not exist yet in the standard.
SCHEMA_ORG = rdflib.Namespace("https://schema.org/")
SCHEMA_ORG_KEY = lambda ctx: SCHEMA_ORG.key if ctx.is_v0() else ML_COMMONS(ctx)["key"]
SCHEMA_ORG_FILE_OBJECT = lambda ctx: (
    SCHEMA_ORG.FileObject if ctx.is_v0() else ML_COMMONS(ctx)["FileObject"]
)
SCHEMA_ORG_FILE_SET = lambda ctx: (
    SCHEMA_ORG.FileSet if ctx.is_v0() else ML_COMMONS(ctx)["FileSet"]
)
SCHEMA_ORG_MD5 = lambda ctx: SCHEMA_ORG.md5 if ctx.is_v0() else ML_COMMONS(ctx)["md5"]

TO_CROISSANT = lambda ctx: {
    ML_COMMONS_CITE_AS(ctx): "cite_as",
    ML_COMMONS_COLUMN(ctx): "csv_column",
    ML_COMMONS_DATA_TYPE(ctx): "data_type",
    ML_COMMONS_DATA(ctx): "data",
    ML_COMMONS_EXTRACT(ctx): "extract",
    ML_COMMONS_FIELD(ctx): "field",
    ML_COMMONS_FILE_PROPERTY(ctx): "file_property",
    ML_COMMONS_FORMAT(ctx): "format",
    ML_COMMONS_INCLUDES(ctx): "includes",
    ML_COMMONS_IS_LIVE_DATASET(ctx): "is_live_dataset",
    ML_COMMONS_JSON_PATH(ctx): "json_path",
    ML_COMMONS_REFERENCES(ctx): "references",
    ML_COMMONS_REGEX(ctx): "regex",
    ML_COMMONS_REPLACE(ctx): "replace",
    ML_COMMONS_SEPARATOR(ctx): "separator",
    ML_COMMONS_SOURCE(ctx): "source",
    ML_COMMONS_TRANSFORM(ctx): "transforms",
    DCTERMS_CONFORMS_TO: "conforms_to",
    SCHEMA_ORG_CONTAINED_IN: "contained_in",
    SCHEMA_ORG_CONTENT_SIZE: "content_size",
    SCHEMA_ORG_CONTENT_URL: "content_url",
    SCHEMA_ORG_CREATOR: "creators",
    SCHEMA_ORG_DATE_CREATED: "date_created",
    SCHEMA_ORG_DATE_MODIFIED: "date_modified",
    SCHEMA_ORG_DATE_PUBLISHED: "date_published",
    SCHEMA_ORG_DESCRIPTION: "description",
    SCHEMA_ORG_DISTRIBUTION: "distribution",
    SCHEMA_ORG_ENCODING_FORMAT: "encoding_format",
    SCHEMA_ORG_KEYWORDS: "keywords",
    SCHEMA_ORG_LICENSE: "license",
    SCHEMA_ORG_MD5: "md5",
    SCHEMA_ORG_NAME: "name",
    SCHEMA_ORG_PUBLISHER: "publisher",
    SCHEMA_ORG_SAME_AS: "sameAs",
    SCHEMA_ORG_SHA256: "sha256",
    SCHEMA_ORG_URL: "url",
    SCHEMA_ORG_VERSION: "version",
}

FROM_CROISSANT = lambda ctx: {v: k for k, v in TO_CROISSANT(ctx).items()}

# Environment variables
DEFAULT_CROISSANT_CACHE = "~/.cache/croissant"
CROISSANT_CACHE = epath.Path(
    os.getenv("CROISSANT_CACHE", DEFAULT_CROISSANT_CACHE)
).expanduser()
DOWNLOAD_PATH = CROISSANT_CACHE / "download"
EXTRACT_PATH = CROISSANT_CACHE / "extract"
CROISSANT_GIT_USERNAME = "CROISSANT_GIT_USERNAME"
CROISSANT_GIT_PASSWORD = "CROISSANT_GIT_PASSWORD"
CROISSANT_BASIC_AUTH_USERNAME = "CROISSANT_BASIC_AUTH_USERNAME"
CROISSANT_BASIC_AUTH_PASSWORD = "CROISSANT_BASIC_AUTH_PASSWORD"


class EncodingFormat:
    """Supported MIME Types in Croissant.

    We inherit the wrong naming `encodingFormat` from https://schema.org/encodingFormat.
    """

    CSV = "text/csv"
    GIT = "git+https"
    JPG = "image/jpeg"
    JSON = "application/json"
    JSON_LINES = "application/jsonlines"
    MP3 = "audio/mpeg"
    PARQUET = "application/x-parquet"
    TEXT = "text/plain"
    TSV = "text/tab-separated-values"
    TAR = "application/x-tar"
    ZIP = "application/zip"


class DataType:
    """Data types supported by Croissant."""

    AUDIO_OBJECT = namespace.SDO.AudioObject
    BOOL = namespace.SDO.Boolean
    BOUNDING_BOX = ML_COMMONS_V_1_0.BoundingBox
    DATE = namespace.SDO.Date
    FLOAT = namespace.SDO.Float
    IMAGE_OBJECT = namespace.SDO.ImageObject
    INTEGER = namespace.SDO.Integer
    SPLIT = ML_COMMONS_V_1_0.Split
    TEXT = namespace.SDO.Text
    URL = namespace.SDO.URL
