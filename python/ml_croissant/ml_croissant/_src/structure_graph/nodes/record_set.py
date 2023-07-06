"""RecordSet module."""

from collections.abc import Mapping
import dataclasses
from typing import Any

from ml_croissant._src.structure_graph.base_node import Node


@dataclasses.dataclass(frozen=True)
class RecordSet(Node):
    """Nodes to describe a dataset RecordSet."""

    # `data` is still a point of discussion in the format, because JSON-LD does not
    # accept arbitrary JSON. All keys are interpreted with respect to the RDF context.
    data: list[Mapping[str, Any]] | None = None
    description: str | None = None
    key: str | None = None
    name: str = ""

    def __post_init__(self):
        self.assert_has_mandatory_properties("name")
        self.assert_has_optional_properties("description")
