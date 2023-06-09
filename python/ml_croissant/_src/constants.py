"""constants module."""

import rdflib

# MLCommons-defined URIs (still draft).
ML_COMMONS_APPLY_TRANSFORM = rdflib.term.URIRef(
    "http://mlcommons.org/schema/applyTransform"
)
ML_COMMONS_DATA = rdflib.term.URIRef("http://mlcommons.org/schema/data")
ML_COMMONS_DATA_TYPE = rdflib.term.URIRef("http://mlcommons.org/schema/dataType")
ML_COMMONS_FORMAT = rdflib.term.URIRef("http://mlcommons.org/schema/format")
ML_COMMONS_FIELD = rdflib.term.URIRef("http://mlcommons.org/schema/Field")
ML_COMMONS_INCLUDES = rdflib.term.URIRef("http://mlcommons.org/schema/includes")
ML_COMMONS_RECORD_SET = rdflib.term.URIRef("http://mlcommons.org/schema/RecordSet")
ML_COMMONS_REFERENCES = rdflib.term.URIRef("http://mlcommons.org/schema/references")
ML_COMMONS_REGEX = rdflib.term.URIRef("http://mlcommons.org/schema/regex")
ML_COMMONS_SOURCE = rdflib.term.URIRef("http://mlcommons.org/schema/source")
ML_COMMONS_SUB_FIELD = rdflib.term.URIRef("http://mlcommons.org/schema/SubField")

# RDF standard URIs.
# For "@type" key:
RDF_TYPE = rdflib.term.URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")

# Schema.org standard URIs.
SCHEMA_ORG_CITATION = rdflib.term.URIRef("https://schema.org/citation")
SCHEMA_ORG_CONTAINED_IN = rdflib.term.URIRef("https://schema.org/containedIn")
SCHEMA_ORG_CONTENT_SIZE = rdflib.term.URIRef("https://schema.org/contentSize")
SCHEMA_ORG_CONTENT_URL = rdflib.term.URIRef("https://schema.org/contentUrl")
SCHEMA_ORG_DATASET = rdflib.URIRef("https://schema.org/Dataset")
SCHEMA_ORG_DATA_TYPE_BOOL = rdflib.term.URIRef("https://schema.org/Boolean")
SCHEMA_ORG_DATA_TYPE_DATE = rdflib.term.URIRef("https://schema.org/Date")
SCHEMA_ORG_DATA_TYPE_FLOAT = rdflib.term.URIRef("https://schema.org/Float")
SCHEMA_ORG_DATA_TYPE_INTEGER = rdflib.term.URIRef("https://schema.org/Integer")
SCHEMA_ORG_DATA_TYPE_TEXT = rdflib.term.URIRef("https://schema.org/Text")
SCHEMA_ORG_DATA_TYPE_URL = rdflib.term.URIRef("https://schema.org/URL")
SCHEMA_ORG_DESCRIPTION = rdflib.term.URIRef("https://schema.org/description")
SCHEMA_ORG_DISTRIBUTION = rdflib.term.URIRef("https://schema.org/distribution")
SCHEMA_ORG_EMAIL = rdflib.term.URIRef("https://schema.org/email")
SCHEMA_ORG_ENCODING_FORMAT = rdflib.term.URIRef("https://schema.org/encodingFormat")
SCHEMA_ORG_LICENSE = rdflib.term.URIRef("https://schema.org/license")
SCHEMA_ORG_NAME = rdflib.term.URIRef("https://schema.org/name")
SCHEMA_ORG_SHA256 = rdflib.term.URIRef("https://schema.org/sha256")
SCHEMA_ORG_URL = rdflib.term.URIRef("https://schema.org/url")

# Schema.org URIs that do not exist yet in the standard.
SCHEMA_ORG_FILE_OBJECT = rdflib.term.URIRef("https://schema.org/FileObject")
SCHEMA_ORG_FILE_SET = rdflib.term.URIRef("https://schema.org/FileSet")
SCHEMA_ORG_MD5 = rdflib.term.URIRef("https://schema.org/md5")

TO_CROISSANT = {
    ML_COMMONS_APPLY_TRANSFORM: "apply_transform",
    ML_COMMONS_DATA_TYPE: "data_type",
    ML_COMMONS_DATA: "data",
    ML_COMMONS_FORMAT: "format",
    ML_COMMONS_INCLUDES: "includes",
    ML_COMMONS_REFERENCES: "references",
    ML_COMMONS_REGEX: "regex",
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
