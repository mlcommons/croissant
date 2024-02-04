"""constants module."""

# flake8: noqa

from etils import epath
import rdflib
from rdflib import namespace

# MLCommons-defined URIs.
ML_COMMONS_V_0_8 = rdflib.Namespace("http://mlcommons.org/schema/")
ML_COMMONS_V_1_0 = rdflib.Namespace("http://mlcommons.org/croissant/")


# ctx: Context is untyped to avoid cyclic dependencies. A unit test tests the behaviour.
def ML_COMMONS(ctx) -> rdflib.Namespace:
    """Switches the main Croissant namespace according to the version."""
    if ctx.is_v0():  # pytype: disable=attribute-error
        return ML_COMMONS_V_0_8
    else:
        return ML_COMMONS_V_1_0


def ML_COMMONS_COLUMN(ctx): return ML_COMMONS(ctx).column
def ML_COMMONS_DATA(ctx): return ML_COMMONS(ctx).data
def ML_COMMONS_DATA_BIASES(ctx): return ML_COMMONS(ctx).dataBiases
def ML_COMMONS_DATA_COLLECTION(ctx): return ML_COMMONS(ctx).dataCollection
def ML_COMMONS_DATA_TYPE(ctx): return ML_COMMONS(ctx).dataType
def ML_COMMONS_DATA_TYPE_BOUNDING_BOX(ctx): return ML_COMMONS(ctx).BoundingBox
def ML_COMMONS_EXTRACT(ctx): return ML_COMMONS(ctx).extract
def ML_COMMONS_FILE_PROPERTY(ctx): return ML_COMMONS(ctx).fileProperty
def ML_COMMONS_FIELD(ctx): return ML_COMMONS(ctx).field
def ML_COMMONS_FIELD_TYPE(ctx): return ML_COMMONS(ctx).Field
def ML_COMMONS_FILE_OBJECT(ctx): return ML_COMMONS(ctx).fileObject
def ML_COMMONS_FILE_SET(ctx): return ML_COMMONS(ctx).fileSet
# ML_COMMONS.format is understood as the `format` method on the class Namespace.
def ML_COMMONS_FORMAT(ctx): return ML_COMMONS(ctx)["format"]
def ML_COMMONS_INCLUDES(ctx): return ML_COMMONS(ctx).includes
def ML_COMMONS_IS_ENUMERATION(ctx): return ML_COMMONS(ctx).isEnumeration
def ML_COMMONS_JSON_PATH(ctx): return ML_COMMONS(ctx).jsonPath
def ML_COMMONS_PARENT_FIELD(ctx): return ML_COMMONS(ctx).parentField
def ML_COMMONS_PATH(ctx): return ML_COMMONS(ctx).path


def ML_COMMONS_PERSONAL_SENSITVE_INFORMATION(ctx): return ML_COMMONS(
    ctx
).personalSensitiveInformation
def ML_COMMONS_RECORD_SET(ctx): return ML_COMMONS(ctx).recordSet
def ML_COMMONS_RECORD_SET_TYPE(ctx): return ML_COMMONS(ctx).RecordSet
def ML_COMMONS_REFERENCES(ctx): return ML_COMMONS(ctx).references
def ML_COMMONS_REGEX(ctx): return ML_COMMONS(ctx).regex
def ML_COMMONS_REPEATED(ctx): return ML_COMMONS(ctx).repeated
# ML_COMMONS.replace is understood as the `replace` method on the class Namespace.
def ML_COMMONS_REPLACE(ctx): return ML_COMMONS(ctx)["replace"]
def ML_COMMONS_SEPARATOR(ctx): return ML_COMMONS(ctx).separator
def ML_COMMONS_SOURCE(ctx): return ML_COMMONS(ctx).source
def ML_COMMONS_SUB_FIELD(ctx): return ML_COMMONS(ctx).subField
def ML_COMMONS_SUB_FIELD_TYPE(ctx): return ML_COMMONS(ctx).SubField
def ML_COMMONS_TRANSFORM(ctx): return ML_COMMONS(ctx).transform

#  RAI


def ML_COMMONS_RAI_DATA_COLLECTION(ctx): return ML_COMMONS(ctx).dataCollection


def ML_COMMONS_RAI_DATA_COLLECTION_TYPE(
    ctx): return ML_COMMONS(ctx).dataCollectionType


def ML_COMMONS_RAI_DATA_COLLECTION_TYPE_OTHERS(
    ctx): return ML_COMMONS(ctx).dataCollectionTypeOthers


def ML_COMMONS_RAI_DATA_COLLECTION_MISSING_DATA(
    ctx): return ML_COMMONS(ctx).dataCollectionMissingData


def ML_COMMONS_RAI_DATA_COLLECTION_RAW_DATA(
    ctx): return ML_COMMONS(ctx).dataCollectionRawData


def ML_COMMONS_RAI_DATA_COLLECTION_TIMEFRAME_START(
    ctx): return ML_COMMONS(ctx).dataCollectionTimeFrameStart


def ML_COMMONS_RAI_DATA_COLLECTION_TIMEFRAME_END(
    ctx): return ML_COMMONS(ctx).dataCollectionTimeFrameEnd


def ML_COMMONS_RAI_DATA_PREPROCESSING_IMPUTATION(
    ctx): return ML_COMMONS(ctx).dataPreprocessingImputations


def ML_COMMONS_RAI_DATA_PREPROCESSING_PROTOCOL(
    ctx): return ML_COMMONS(ctx).dataPreprocessingProtocol


def ML_COMMONS_RAI_DATA_PREPROCESSING_MANIPULATION(
    ctx): return ML_COMMONS(ctx).dataPreprocessingManipulation


def ML_COMMONS_RAI_DATA_ANNOTATION_PROTOCOL(
    ctx): return ML_COMMONS(ctx).dataAnnotationProtocol


def ML_COMMONS_RAI_DATA_ANNOTATION_PLATFORM(
    ctx): return ML_COMMONS(ctx).dataAnnotationPlatform


def ML_COMMONS_RAI_DATA_ANNOTATION_ANALYSIS(
    ctx): return ML_COMMONS(ctx).dataAnnotationAnalysis


def ML_COMMONS_RAI_DATA_ANNOTATION_PERITEM(
    ctx): return ML_COMMONS(ctx).dataAnnotationPerItem


def ML_COMMONS_RAI_DATA_ANNOTATION_DEMOGRAPHICS(
    ctx): return ML_COMMONS(ctx).dataAnnotationDemographics
def ML_COMMONS_RAI_DATA_ANNOTATION_TOOLS(
    ctx): return ML_COMMONS(ctx).dataAnnotationTools


def ML_COMMONS_RAI_DATA_USECASES(ctx): return ML_COMMONS(ctx).dataUseCases
def ML_COMMONS_RAI_DATA_BIAS(ctx): return ML_COMMONS(ctx).dataBias
def ML_COMMONS_RAI_DATA_LIMITATION(ctx): return ML_COMMONS(ctx).dataLimitations
def ML_COMMONS_RAI_DATA_SOCIAL_IMPACT(
    ctx): return ML_COMMONS(ctx).dataSocialImpact


def ML_COMMONS_RAI_DATA_SENSITIVE(ctx): return ML_COMMONS(ctx).dataSensitive


def ML_COMMONS_RAI_DATA_MAINTENANCE(
    ctx): return ML_COMMONS(ctx).dataMaintenance


# RDF standard URIs.
# For "@type" key:
RDF_TYPE = namespace.RDF.type

# Dublin Core terms standard URIs.
DCTERMS = "http://purl.org/dc/terms/"
DCTERMS_CONFORMS_TO = namespace.DCTERMS.conformsTo

# Schema.org standard URIs.
SCHEMA_ORG_CITATION = namespace.SDO.citation
SCHEMA_ORG_CONTAINED_IN = namespace.SDO.containedIn
SCHEMA_ORG_CONTENT_SIZE = namespace.SDO.contentSize
SCHEMA_ORG_CONTENT_URL = namespace.SDO.contentUrl
SCHEMA_ORG_CREATOR = namespace.SDO.creator
SCHEMA_ORG_DATE_PUBLISHED = namespace.SDO.datePublished
SCHEMA_ORG_DATASET = namespace.SDO.Dataset
SCHEMA_ORG_DESCRIPTION = namespace.SDO.description
SCHEMA_ORG_DISTRIBUTION = namespace.SDO.distribution
SCHEMA_ORG_EMAIL = namespace.SDO.email
SCHEMA_ORG_ENCODING_FORMAT = namespace.SDO.encodingFormat
SCHEMA_ORG_LICENSE = namespace.SDO.license
SCHEMA_ORG_NAME = namespace.SDO.name
SCHEMA_ORG_SHA256 = namespace.SDO.sha256
SCHEMA_ORG_URL = namespace.SDO.url
SCHEMA_ORG_VERSION = namespace.SDO.version

# Schema.org URIs that do not exist yet in the standard.
SCHEMA_ORG = rdflib.Namespace("https://schema.org/")
SCHEMA_ORG_KEY = SCHEMA_ORG.key
SCHEMA_ORG_FILE_OBJECT = SCHEMA_ORG.FileObject
SCHEMA_ORG_FILE_SET = SCHEMA_ORG.FileSet
SCHEMA_ORG_MD5 = SCHEMA_ORG.md5


def TO_CROISSANT(ctx): return {
    ML_COMMONS_TRANSFORM(ctx): "transforms",
    ML_COMMONS_COLUMN(ctx): "csv_column",
    ML_COMMONS_DATA_TYPE(ctx): "data_type",
    ML_COMMONS_DATA(ctx): "data",
    ML_COMMONS_EXTRACT(ctx): "extract",
    ML_COMMONS_FIELD(ctx): "field",
    ML_COMMONS_FILE_PROPERTY(ctx): "file_property",
    ML_COMMONS_FORMAT(ctx): "format",
    ML_COMMONS_INCLUDES(ctx): "includes",
    ML_COMMONS_JSON_PATH(ctx): "json_path",
    ML_COMMONS_REFERENCES(ctx): "references",
    ML_COMMONS_REGEX(ctx): "regex",
    ML_COMMONS_REPLACE(ctx): "replace",
    ML_COMMONS_SEPARATOR(ctx): "separator",
    ML_COMMONS_SOURCE(ctx): "source",
    DCTERMS_CONFORMS_TO: "conforms_to",
    SCHEMA_ORG_CITATION: "citation",
    SCHEMA_ORG_CONTAINED_IN: "contained_in",
    SCHEMA_ORG_CONTENT_SIZE: "content_size",
    SCHEMA_ORG_CONTENT_URL: "content_url",
    SCHEMA_ORG_DESCRIPTION: "description",
    SCHEMA_ORG_DISTRIBUTION: "distribution",
    SCHEMA_ORG_ENCODING_FORMAT: "encoding_format",
    SCHEMA_ORG_LICENSE: "license",
    SCHEMA_ORG_MD5: "md5",
    SCHEMA_ORG_NAME: "name",
    SCHEMA_ORG_SHA256: "sha256",
    SCHEMA_ORG_URL: "url",
    SCHEMA_ORG_VERSION: "version",
}


def FROM_CROISSANT(ctx): return {v: k for k, v in TO_CROISSANT(ctx).items()}


# Environment variables
CROISSANT_CACHE = epath.Path("~/.cache/croissant").expanduser()
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
    JSON = "application/json"
    JSON_LINES = "application/jsonlines"
    PARQUET = "application/x-parquet"
    TEXT = "text/plain"
    TSV = "text/tsv"
    TAR = "application/x-tar"
    ZIP = "application/zip"


class DataType:
    """Data types supported by Croissant."""

    BOOL = namespace.SDO.Boolean
    def BOUNDING_BOX(ctx): return ML_COMMONS(ctx).BoundingBox
    DATE = namespace.SDO.Date
    FLOAT = namespace.SDO.Float
    IMAGE_OBJECT = namespace.SDO.ImageObject
    INTEGER = namespace.SDO.Integer
    TEXT = namespace.SDO.Text
    URL = namespace.SDO.URL
