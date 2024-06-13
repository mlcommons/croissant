"""RDF module to represent all things related to the Resource Description Framework."""

from __future__ import annotations

import dataclasses
import functools
from typing import Any

from absl import logging
from rdflib import term

from mlcroissant._src.core.types import Json


def get_context(json_: Json) -> Json:
    """Returns the context and raises an error if it is not a dictionary as expected."""
    context = json_.get("@context", {})
    if not isinstance(context, dict):
        raise ValueError("@context should be a dictionary. Got: {existing_context}")
    return context


def make_context(ctx=None, **kwargs):
    """Returns the JSON-LD @context with additional keys."""
    context = {
        "@language": "en",
        "@vocab": "https://schema.org/",
        "citeAs": "cr:citeAs",
        "column": "cr:column",
        "conformsTo": "dct:conformsTo",
        "cr": "http://mlcommons.org/croissant/",
        "rai": "http://mlcommons.org/croissant/RAI/",
        "data": {"@id": "cr:data", "@type": "@json"},
        "dataType": {"@id": "cr:dataType", "@type": "@vocab"},
        "dct": "http://purl.org/dc/terms/",
        "examples": {"@id": "cr:examples", "@type": "@json"},
        "extract": "cr:extract",
        "field": "cr:field",
        "fileProperty": "cr:fileProperty",
        "fileObject": "cr:fileObject",
        "fileSet": "cr:fileSet",
        "format": "cr:format",
        "includes": "cr:includes",
        "isLiveDataset": "cr:isLiveDataset",
        "jsonPath": "cr:jsonPath",
        "key": "sc:key" if ctx is not None and ctx.is_v0() else "cr:key",
        "md5": "sc:md5" if ctx is not None and ctx.is_v0() else "cr:md5",
        "parentField": "cr:parentField",
        "path": "cr:path",
        "recordSet": "cr:recordSet",
        "references": "cr:references",
        "regex": "cr:regex",
        "repeated": "cr:repeated",
        "replace": "cr:replace",
        "sc": "https://schema.org/",
        "separator": "cr:separator",
        "source": "cr:source",
        "subField": "cr:subField",
        "transform": "cr:transform",
        **kwargs,
    }
    return {key: value for key, value in context.items() if value is not None}


@dataclasses.dataclass(eq=False, repr=False)
class Rdf:
    """RDF-specific vocabulary on the metadata."""

    context: Json = dataclasses.field(default_factory=make_context)

    @classmethod
    def from_json(cls, ctx, json: Json) -> Rdf:
        """Creates a `Rdf` from JSON."""
        context = get_context(json)
        # Keys that are in the standard @context, but not in the current @context.
        different_keys = make_context(ctx).keys() - context.keys()
        if different_keys:
            logging.warning(
                "WARNING: The JSON-LD `@context` is not standard. Refer to the"
                " official @context (e.g., from the example datasets in"
                " https://github.com/mlcommons/croissant/tree/main/datasets/1.0). The"
                f" different keys are: {different_keys}"
            )
        return cls(context=context)

    @functools.cache
    def reverse_context(self) -> Json:
        """Reverses the context dictionary.

        - context = "ml"->"http://mlcommons.org/schema"
        - reverse_context = "http://mlcommons.org/schema"->"ml"
        """
        reversed_context = {}

        def add_mapping(k: str, v: Any):
            if not isinstance(v, str):
                return
            # cr:transform -> transform
            reversed_context[v] = k
            splits = v.split(":")
            abbreviation = splits[0]
            if url := self.abbreviations().get(abbreviation):
                if len(splits) > 2:
                    raise ValueError("Key in @context contains several colons (:)")
                value = f"{url}{splits[1]}"
                # https://mlcommons.org/croissant -> transform
                reversed_context[value] = k

        for k, v in self.context.items():
            if isinstance(v, str):
                add_mapping(k, v)
            elif isinstance(v, dict):
                add_mapping(k, v.get("@id"))
        return reversed_context

    @functools.cache
    def abbreviations(self) -> Json:
        """Lists all abbreviations, eg "ml"->"http://mlcommons.org/schema"."""
        return {
            k: v
            for k, v in reversed(self.context.items())
            if isinstance(v, str) and (v.startswith("https") or v.startswith("http"))
        }

    @functools.cache
    def shorten_value(self, value: str) -> str:
        """Shortens a value according to the context if possible."""
        for abbreviation, url in self.abbreviations().items():
            if value.startswith(url):
                return value.replace(url, f"{abbreviation}:")
        return value

    @functools.cache
    def shorten_key(self, key: str | term.URIRef) -> str:
        """Shortens a key according to the context if possible.

        Keys and values are shortened differently in Croissant. For example, as a value
        https://schema.org/FileObject will be `sc:FileObject`, but as a key
        https://schema.org/fileObject will be `fileObject`.
        """
        key = str(key)
        # 1. Try to shorten with the vocab:
        vocab = self.context.get("@vocab")
        if isinstance(vocab, str) and key.startswith(vocab):
            return key.replace(vocab, "", 1)
        # 2. Try to shorten with the context:
        if short := self.reverse_context().get(key):
            return short
        return self.shorten_value(key)
