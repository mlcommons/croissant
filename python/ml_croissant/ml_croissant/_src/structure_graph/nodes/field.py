"""Field module."""

from collections.abc import Mapping
import dataclasses
from typing import Any

from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.nodes.source import Source
import networkx as nx


@dataclasses.dataclass(frozen=True, repr=False)
class Field(Node):
    """Nodes to describe a dataset Field."""

    data: list[Mapping[str, Any]] | None = None
    croissant_data_type: str | None = None
    description: str | None = None
    has_sub_fields: bool | None = None
    name: str = ""
    references: Source = dataclasses.field(default_factory=Source)
    source: Source = dataclasses.field(default_factory=Source)

    def check(self):
        self.assert_has_mandatory_properties("name")
        self.assert_has_optional_properties("description")
        # TODO(marcenacp): check that `data` has the expected form if it exists.

    def data_type(self, graph: nx.MultiDiGraph) -> str | None:
        if self.croissant_data_type is not None:
            return self.croissant_data_type
        parent = next(graph.predecessors(self), None)
        if parent is None or not isinstance(parent, Field):
            self.add_error(
                "The field does not specify any dataType, neither does any of its"
                " predecessor."
            )
            return None
        return parent.data_type(graph)
