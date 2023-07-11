"""RecordSet module."""

from collections.abc import Mapping
import dataclasses
from typing import Any

from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.nodes.source import Source


@dataclasses.dataclass(frozen=True, repr=False)
class RecordSet(Node):
    """Nodes to describe a dataset RecordSet."""

    # `data` is passed as a string for the moment, because dicts and lists are not hashable.
    data: str | None = None
    description: str | None = None
    key: str | None = None
    name: str = ""
    source: Source | None = None

    def check(self):
        self.assert_has_mandatory_properties("name")
        self.assert_has_optional_properties("description")
        # TODO(marcenacp): check for data integrity?
