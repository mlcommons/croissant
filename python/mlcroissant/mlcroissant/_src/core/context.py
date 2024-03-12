"""Global context."""

from __future__ import annotations

import dataclasses
import enum
import typing
from typing import Any, Mapping

from etils import epath
import networkx as nx

from mlcroissant._src.core.issues import Issues
from mlcroissant._src.core.rdf import Rdf

if typing.TYPE_CHECKING:
    from mlcroissant._src.structure_graph.base_node import Node


class CroissantVersion(enum.Enum):
    """Major and minor versions of the Croissant standard."""

    V_0_8 = "http://mlcommons.org/croissant/0.8"
    V_1_0 = "http://mlcommons.org/croissant/1.0"

    @classmethod
    def from_jsonld(cls, ctx: Context, jsonld: Any) -> CroissantVersion:
        """Builds the class from the JSON-LD."""
        if isinstance(jsonld, CroissantVersion):
            return jsonld
        elif not jsonld:
            return CroissantVersion.V_0_8
        else:
            try:
                return CroissantVersion(jsonld)
            except ValueError:
                ctx.issues.add_error(
                    "conformsTo should be a string or a CroissantVersion. Got:"
                    f" {jsonld}"
                )
                return CroissantVersion.V_0_8

    def to_json(self) -> str | None:
        """Serializes back to JSON-LD."""
        if self == CroissantVersion.V_0_8:
            # In 0.8, the field conformsTo doesn't exist yet.
            return None
        return self.value

    def __lt__(self, other: CroissantVersion) -> bool:
        """Implements CroissantVersion.V_0_8 < CroissantVersion.V_1_0."""
        return self.value < other.value

    def __le__(self, other: CroissantVersion) -> bool:
        """Implements CroissantVersion.V_0_8 <= CroissantVersion.V_1_0."""
        return self.value <= other.value

    def __gt__(self, other: CroissantVersion) -> bool:
        """Implements CroissantVersion.V_1_0 > CroissantVersion.V_0_8."""
        return self.value > other.value

    def __ge__(self, other: CroissantVersion) -> bool:
        """Implements CroissantVersion.V_1_0 >= CroissantVersion.V_0_8."""
        return self.value >= other.value


@dataclasses.dataclass
class Context:
    """A global context in the application to store commonly used objects."""

    issues: Issues = dataclasses.field(default_factory=Issues)
    folder: epath.Path | None = None
    graph: nx.MultiDiGraph = dataclasses.field(
        default_factory=nx.MultiDiGraph, compare=False, init=False, hash=False
    )
    rdf: Rdf = dataclasses.field(default_factory=Rdf, hash=False)
    mapping: Mapping[str, epath.Path] = dataclasses.field(
        default_factory=dict, hash=False
    )
    conforms_to: CroissantVersion = CroissantVersion.V_1_0
    is_live_dataset: bool | None = None

    def __post_init__(self):
        """Standardizes conforms_to."""
        self.conforms_to = CroissantVersion.from_jsonld(self, self.conforms_to)

    def copy(self, **changes) -> Context:
        """Copies and replaces all changes."""
        return dataclasses.replace(self, **changes)

    def is_v0(self):
        """Whether the JSON-LD conforms to Croissant v0.8 or lower."""
        return self.conforms_to < CroissantVersion.V_1_0

    def node_by_uuid(self, uuid: str | None) -> Node | None:
        """Retrieves a node in the graph by its UID."""
        for node in self.graph.nodes():
            if node.uuid == uuid:  # pytype: disable=attribute-error
                return node  # pytype: disable=bad-return-type
        return None
