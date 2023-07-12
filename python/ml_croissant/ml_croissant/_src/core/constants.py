"""constants module."""

from etils import epath
import rdflib
from rdflib import namespace


# MLCommons-defined URIs (still draft).
ML_COMMONS = rdflib.Namespace("http://mlcommons.org/schema/")
ML_COMMONS_APPLY_TRANSFORM = ML_COMMONS.applyTransform
ML_COMMONS_DATA = ML_COMMONS.data
ML_COMMONS_DATA_TYPE = ML_COMMONS.dataType
# ML_COMMONS.format is understood as the `format` method on the class Namespace.
ML_COMMONS_FORMAT = rdflib.term.URIRef("http://mlcommons.org/schema/format")
ML_COMMONS_FIELD = ML_COMMONS.Field
ML_COMMONS_INCLUDES = ML_COMMONS.includes
ML_COMMONS_RECORD_SET = ML_COMMONS.RecordSet
ML_COMMONS_REFERENCES = ML_COMMONS.references
ML_COMMONS_REGEX = ML_COMMONS.regex
# ML_COMMONS.replace is understood as the `replace` method on the class Namespace.
ML_COMMONS_REPLACE = rdflib.term.URIRef("http://mlcommons.org/schema/replace")
ML_COMMONS_SEPARATOR = ML_COMMONS.separator
ML_COMMONS_SOURCE = ML_COMMONS.source
ML_COMMONS_SUB_FIELD = ML_COMMONS.SubField

# RDF standard URIs.
# For "@type" key:
RDF_TYPE = namespace.RDF.type

# Schema.org standard URIs.
SCHEMA_ORG_CITATION = namespace.SDO.citation
SCHEMA_ORG_CONTAINED_IN = namespace.SDO.containedIn
SCHEMA_ORG_CONTENT_SIZE = namespace.SDO.contentSize
SCHEMA_ORG_CONTENT_URL = namespace.SDO.contentUrl
SCHEMA_ORG_DATASET = namespace.SDO.Dataset
SCHEMA_ORG_DATA_TYPE_BOOL = namespace.SDO.Boolean
SCHEMA_ORG_DATA_TYPE_DATE = namespace.SDO.Date
SCHEMA_ORG_DATA_TYPE_FLOAT = namespace.SDO.Float
SCHEMA_ORG_DATA_TYPE_INTEGER = namespace.SDO.Integer
SCHEMA_ORG_DATA_TYPE_TEXT = namespace.SDO.Text
SCHEMA_ORG_DATA_TYPE_URL = namespace.SDO.URL
SCHEMA_ORG_DESCRIPTION = namespace.SDO.description
SCHEMA_ORG_DISTRIBUTION = namespace.SDO.distribution
SCHEMA_ORG_EMAIL = namespace.SDO.email
SCHEMA_ORG_ENCODING_FORMAT = namespace.SDO.encodingFormat
SCHEMA_ORG_LICENSE = namespace.SDO.license
SCHEMA_ORG_NAME = namespace.SDO.name
SCHEMA_ORG_SHA256 = namespace.SDO.sha256
SCHEMA_ORG_URL = namespace.SDO.url

# Schema.org URIs that do not exist yet in the standard.
SCHEMA_ORG = rdflib.Namespace("https://schema.org/")
SCHEMA_ORG_FILE_OBJECT = SCHEMA_ORG.FileObject
SCHEMA_ORG_FILE_SET = SCHEMA_ORG.FileSet
SCHEMA_ORG_MD5 = SCHEMA_ORG.md5

TO_CROISSANT = {
    ML_COMMONS_APPLY_TRANSFORM: "apply_transform",
    ML_COMMONS_DATA_TYPE: "field_data_type",
    ML_COMMONS_DATA: "data",
    ML_COMMONS_FORMAT: "format",
    ML_COMMONS_INCLUDES: "includes",
    ML_COMMONS_REFERENCES: "references",
    ML_COMMONS_REGEX: "regex",
    ML_COMMONS_REPLACE: "replace",
    ML_COMMONS_SEPARATOR: "separator",
    ML_COMMONS_SOURCE: "source",
    SCHEMA_ORG_CITATION: "citation",
    SCHEMA_ORG_CONTAINED_IN: "contained_in",
    SCHEMA_ORG_CONTENT_SIZE: "content_size",
    SCHEMA_ORG_CONTENT_URL: "content_url",
    SCHEMA_ORG_DESCRIPTION: "description",
    SCHEMA_ORG_ENCODING_FORMAT: "encoding_format",
    SCHEMA_ORG_LICENSE: "license",
    SCHEMA_ORG_MD5: "md5",
    SCHEMA_ORG_NAME: "name",
    SCHEMA_ORG_SHA256: "sha256",
    SCHEMA_ORG_URL: "url",
}

FROM_CROISSANT = {v: k for k, v in TO_CROISSANT.items()}

CROISSANT_CACHE = epath.Path("~/.cache/croissant").expanduser()
DOWNLOAD_PATH = CROISSANT_CACHE / "download"
EXTRACT_PATH = CROISSANT_CACHE / "extract"
