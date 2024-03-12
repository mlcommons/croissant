"""Person module."""

from rdflib.namespace import SDO

from mlcroissant._src.core import dataclasses as mlc_dataclasses
from mlcroissant._src.structure_graph.base_node import Node


@mlc_dataclasses.dataclass
class Person(Node):
    """Represents schema.org/Person."""

    JSONLD_TYPE = SDO.Person

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
    email: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="Email address.",
        input_types=[SDO.Text],
        url=SDO.email,
    )
    url: str | None = mlc_dataclasses.jsonld_field(
        default=None,
        description="URL of the item.",
        input_types=[SDO.URL],
        url=SDO.url,
    )
