"""RDF module to represent all things related to the Resource Description Framework."""

from __future__ import annotations

import dataclasses
import functools

from mlcroissant._src.core.json_ld import get_context
from mlcroissant._src.core.json_ld import make_context
from mlcroissant._src.core.types import Json


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
