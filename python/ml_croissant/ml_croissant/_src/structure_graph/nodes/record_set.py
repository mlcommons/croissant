"""RecordSet module."""

from collections.abc import Mapping
import dataclasses
from typing import Any

from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.nodes.source import Source


@dataclasses.dataclass(frozen=True, repr=False)
class RecordSet(Node):
    """Nodes to describe a dataset RecordSet."""

    # `data` is still a point of discussion in the format, because JSON-LD does not
    # accept arbitrary JSON. All keys are interpreted with respect to the RDF context.
    data: list[Mapping[str, Any]] | None = None
    description: str | None = None
    key: str | None = None
    name: str = ""
    source: Source | None = None

    def check(self):
        self.assert_has_mandatory_properties("name")
        self.assert_has_optional_properties("description")
