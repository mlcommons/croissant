"""RDF module to represent all things related to the Resource Description Framework."""

from __future__ import annotations

import dataclasses
import functools

from mlcroissant._src.core.types import Json

BASE_CONTEXT = {
    "@language": "en",
    "@vocab": "https://schema.org/",
    "column": "ml:column",
    "conformsTo": "dct:conformsTo",
    "cr": "http://mlcommons.org/croissant/",
    "data": {"@id": "ml:data", "@type": "@json"},
    "dataBiases": "ml:dataBiases",
    "dataCollection": "ml:dataCollection",
    "dataType": {"@id": "ml:dataType", "@type": "@vocab"},
    "dct": "http://purl.org/dc/terms/",
    "extract": "ml:extract",
    "field": "ml:field",
    "fileProperty": "ml:fileProperty",
    "fileObject": "ml:fileObject",
    "fileSet": "ml:fileSet",
    "format": "ml:format",
    "includes": "ml:includes",
    "isEnumeration": "ml:isEnumeration",
    "jsonPath": "ml:jsonPath",
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


def get_context(json_: Json) -> Json:
    """Returns the context and raises an error if it is not a dictionary as expected."""
    context = json_.get("@context", {})
    if not isinstance(context, dict):
        raise ValueError("@context should be a dictionary. Got: {existing_context}")
    return context


def make_context(**kwargs):
    """Returns the JSON-LD @context with additional keys."""
    return {**BASE_CONTEXT, **kwargs}


@dataclasses.dataclass(eq=False, repr=False)
class Rdf:
    """RDF-specific vocabulary on the metadata."""

    context: Json = dataclasses.field(default_factory=make_context)

    @classmethod
    def from_json(cls, json: Json) -> Rdf:
        """Creates a `Rdf` from JSON."""
        context = get_context(json)
        return cls(context=make_context(**context))

    @functools.cache
    def reverse_context(self) -> Json:
        """Reverses the context dictionary.

        - context = "ml"->"http://mlcommons.org/schema"
        - inverse_context = "http://mlcommons.org/schema"->"ml"
        """
        return {v: k for k, v in self.context.items() if isinstance(v, str)}

    @functools.cache
    def shorten_value(self, value: str) -> str:
        """Shortens a value according to the context if possible."""
        for url, abbreviation in self.reverse_context().items():
            is_url = value.startswith("http://") or value.startswith("https://")
            if is_url and value.startswith(url):
                return value.replace(url, f"{abbreviation}:")
        return value
