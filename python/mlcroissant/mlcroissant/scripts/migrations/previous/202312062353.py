"""Migration: to add the conformsTo field."""

NEW_CONTEXT = {
    "@language": "en",
    "@vocab": "https://schema.org/",
    "column": "ml:column",
    "conformsTo": "dct:conformsTo",
    "data": {"@id": "ml:data", "@type": "@json"},
    "dataBiases": "ml:dataBiases",
    "dataCollection": "ml:dataCollection",
    "dataType": {"@id": "ml:dataType", "@type": "@vocab"},
    "dct": "http://purl.org/dc/terms/",
    "extract": "ml:extract",
    "field": "ml:field",
    "fileProperty": "ml:fileProperty",
    "format": "ml:format",
    "includes": "ml:includes",
    "isEnumeration": "ml:isEnumeration",
    "jsonPath": "ml:jsonPath",
    "ml": "http://mlcommons.org/schema/",
    "parentField": "ml:parentField",
    "path": "ml:path",
    "personalSensitiveInformation": "ml:personalSensitiveInformation",
    "recordSet": "ml:recordSet",
    "references": "ml:references",
    "regex": "ml:regex",
    "repeated": "ml:repeated",
    "replace": "ml:replace",
    "sc": "https://schema.org/",
    "separator": "ml:separator",
    "source": "ml:source",
    "subField": "ml:subField",
    "transform": "ml:transform",
}


def up(json_ld):
    """Up migration to set conformsTo to croissant specs 1.0."""
    json_ld["@context"] = NEW_CONTEXT
    json_ld["conformsTo"] = "http://mlcommons.org/croissant/1.0"
    return json_ld
