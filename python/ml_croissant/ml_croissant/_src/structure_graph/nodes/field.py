"""Field module."""

from collections.abc import Mapping
import dataclasses
from typing import Any

from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.nodes.source import Source

@dataclasses.dataclass(frozen=True, repr=False)
class Field(Node):
    """Nodes to describe a dataset Field."""

    data: list[Mapping[str, Any]] | None = None
    data_type: str | None = None
    description: str | None = None
    has_sub_fields: bool | None = None
    name: str = ""
    references: Source = dataclasses.field(default_factory=Source)
    source: Source = dataclasses.field(default_factory=Source)

    def check(self):
        self.assert_has_mandatory_properties("data_type", "name")
        self.assert_has_optional_properties("description")
        # TODO(marcenacp): check that `data` has the expected form if it exists.
