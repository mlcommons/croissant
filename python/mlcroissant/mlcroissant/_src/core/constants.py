"""constants module."""

from etils import epath
import rdflib
from rdflib import namespace
from rdflib import term

# MLCommons-defined URIs (still draft).
ML_COMMONS = rdflib.Namespace("http://mlcommons.org/schema/")
ML_COMMONS_COLUMN = ML_COMMONS.column
ML_COMMONS_DATA = ML_COMMONS.data
ML_COMMONS_DATA_BIASES = ML_COMMONS.dataBiases
ML_COMMONS_DATA_COLLECTION = ML_COMMONS.dataCollection
ML_COMMONS_DATA_TYPE = ML_COMMONS.dataType
ML_COMMONS_DATA_TYPE_BOUNDING_BOX = ML_COMMONS.BoundingBox
ML_COMMONS_EXTRACT = ML_COMMONS.extract
ML_COMMONS_FILE_PROPERTY = ML_COMMONS.fileProperty
ML_COMMONS_FIELD = ML_COMMONS.field
ML_COMMONS_FIELD_TYPE = ML_COMMONS.Field
# ML_COMMONS.format is understood as the `format` method on the class Namespace.
ML_COMMONS_FORMAT = term.URIRef("http://mlcommons.org/schema/format")
ML_COMMONS_INCLUDES = ML_COMMONS.includes
ML_COMMONS_IS_ENUMERATION = ML_COMMONS.isEnumeration
ML_COMMONS_JSON_PATH = ML_COMMONS.jsonPath
ML_COMMONS_PARENT_FIELD = ML_COMMONS.parentField
ML_COMMONS_PATH = ML_COMMONS.path
ML_COMMONS_PERSONAL_SENSITVE_INFORMATION = ML_COMMONS.personalSensitiveInformation
ML_COMMONS_RECORD_SET = ML_COMMONS.recordSet
ML_COMMONS_RECORD_SET_TYPE = ML_COMMONS.RecordSet
ML_COMMONS_REFERENCES = ML_COMMONS.references
ML_COMMONS_REGEX = ML_COMMONS.regex
ML_COMMONS_REPEATED = ML_COMMONS.repeated
# ML_COMMONS.replace is understood as the `replace` method on the class Namespace.
ML_COMMONS_REPLACE = term.URIRef("http://mlcommons.org/schema/replace")
ML_COMMONS_SEPARATOR = ML_COMMONS.separator
ML_COMMONS_SOURCE = ML_COMMONS.source
ML_COMMONS_SUB_FIELD = ML_COMMONS.subField
ML_COMMONS_SUB_FIELD_TYPE = ML_COMMONS.SubField
ML_COMMONS_TRANSFORM = ML_COMMONS.transform


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

TO_CROISSANT = {
    ML_COMMONS_TRANSFORM: "transforms",
    ML_COMMONS_COLUMN: "csv_column",
    ML_COMMONS_DATA_TYPE: "data_type",
    ML_COMMONS_DATA: "data",
    ML_COMMONS_EXTRACT: "extract",
    ML_COMMONS_FIELD: "field",
    ML_COMMONS_FILE_PROPERTY: "file_property",
    ML_COMMONS_FORMAT: "format",
    ML_COMMONS_INCLUDES: "includes",
    ML_COMMONS_JSON_PATH: "json_path",
    ML_COMMONS_REFERENCES: "references",
    ML_COMMONS_REGEX: "regex",
    ML_COMMONS_REPLACE: "replace",
    ML_COMMONS_SEPARATOR: "separator",
    ML_COMMONS_SOURCE: "source",
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

FROM_CROISSANT = {v: k for k, v in TO_CROISSANT.items()}

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
    BOUNDING_BOX = ML_COMMONS.BoundingBox
    DATE = namespace.SDO.Date
    FLOAT = namespace.SDO.Float
    IMAGE_OBJECT = namespace.SDO.ImageObject
    INTEGER = namespace.SDO.Integer
    TEXT = namespace.SDO.Text
    URL = namespace.SDO.URL
