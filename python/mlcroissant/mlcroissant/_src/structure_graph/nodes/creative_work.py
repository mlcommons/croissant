"""CreativeWork module."""

from rdflib.namespace import SDO

from mlcroissant._src.core import dataclasses as mlc_dataclasses
from mlcroissant._src.structure_graph.base_node import Node


@mlc_dataclasses.dataclass
class CreativeWork(Node):
    """Represents schema.org/CreativeWork."""

    JSONLD_TYPE = SDO.CreativeWork

    name: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="The name of the item.",
        input_types=[SDO.Text],
        url=SDO.name,
    )
    description: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="A description of the item.",
        input_types=[SDO.Text],
        url=SDO.description,
    )
    url: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="URL of the item.",
        input_types=[SDO.URL],
        url=SDO.url,
    )
