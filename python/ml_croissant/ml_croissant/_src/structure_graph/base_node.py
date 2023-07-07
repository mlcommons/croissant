"""Base node module."""

import abc
import dataclasses
import re

import networkx as nx
import rdflib

from ml_croissant._src.core import constants
from ml_croissant._src.core.issues import Context, Issues

ID_REGEX = "[a-zA-Z0-9\\-_\\.]+"
_MAX_ID_LENGTH = 255


@dataclasses.dataclass(frozen=True, repr=False)
class Node(abc.ABC):
    """Structure node in Croissant.

    This generic class will be inherited by the actual Croissant nodes:
    - Field
    - FileObject
    - FileSet
    - Metadata
    - RecordSet

    When building the node, `self.issues` are populated when issues are encountered.

    Args:
        issues: the issues that will be modified in-place.
        graph: The NetworkX RDF graph to validate.
        node: The node in the graph to convert.
        name: The name of the node.
        rdf_id: The RDF @id created by RDFLib.
        uid: Croissant unique identifier. It's the concatenation of the path within
            the Croissant hierarchy. For instance, for a field:
            dataset.name/record_set.name/field.name.
        context: Context of the node in the Croissant hierarchy (dataset, distribution,
            record set, field).

    Usage:

    ```python
    node = Node(issues=issues, graph=graph, node=source)

    # Can access a property of the node:
    citation = node["https://schema.org/citation"]

    # Can check a property exists:
    has_citation = "https://schema.org/citation" in node

    # Can assert features on the node. E.g.:
    node.assert_has_exclusive_properties(
        [[""https://schema.org/sha256"", "https://schema.org/md5"]]
    )
    ```
    """

    issues: Issues
    graph: nx.MultiDiGraph = None
    node: rdflib.term.BNode = None
    name: str = ""
    rdf_id: str | None = None
    uid: str | None = None
    context: Context | None = None

    def __post_init__(self):
        """Checks for `name` (common property between all nodes)."""
        self.assert_has_mandatory_properties("name")
        validate_name(self.issues, self.name)

    @property
    def _edges_from_node(self):
        return self.graph.edges(self.node, keys=True)

    def assert_has_mandatory_properties(self, *mandatory_properties: list[str]):
        """Checks a node in the graph for existing properties with constraints.

        Args:
            mandatory_properties: A list of mandatory properties for the current node.
                If the node doesn't have one, it triggers an error.
        """
        for mandatory_property in mandatory_properties:
            value = getattr(self, mandatory_property)
            if not value:
                error = (
                    f'Property "{constants.FROM_CROISSANT.get(mandatory_property)}" is'
                    " mandatory, but does not exist."
                )
                self.add_error(error)

    def assert_has_optional_properties(self, *optional_properties: list[str]):
        """Checks a node in the graph for existing properties with constraints.

        Args:
            optional_properties: A list of optional properties for the current node. If
                the node doesn't have one, it triggers a warning.
        """
        for optional_property in optional_properties:
            value = getattr(self, optional_property)
            if not value:
                error = (
                    f'Property "{constants.FROM_CROISSANT.get(optional_property)}" is'
                    " recommended, but does not exist."
                )
                self.add_warning(error)

    def assert_has_exclusive_properties(self, *exclusive_properties: list[list[str]]):
        """Checks a node in the graph for existing properties with constraints.

        Args:
            exclusive_properties: A list of list of exclusive properties: the current
                node should have at least one.
        """
        for possible_exclusive_properties in exclusive_properties:
            if not there_exists_at_least_one_property(
                self, possible_exclusive_properties
            ):
                error = (
                    "At least one of these properties should be defined:"
                    f" {possible_exclusive_properties}."
                )
                self.add_error(error)

    def add_error(self, error: str):
        """Adds a new error."""
        self.issues.add_error(error, self.context)

    def add_warning(self, warning: str):
        """Adds a new warning."""
        self.issues.add_warning(warning, self.context)

    @abc.abstractmethod
    def check(self):
        raise NotImplementedError

    def __repr__(self):
        attributes = self.__dict__.copy()
        attributes_to_remove = ["context", "graph", "issues", "node"]
        for attribute in attributes_to_remove:
            if attribute in attributes:
                del attributes[attribute]
        attributes_items = sorted(list(attributes.items()))
        attributes_str = ", ".join(f"{key}={value}" for key, value in attributes_items)
        return f"{self.__class__.__name__}({attributes_str})"


def validate_name(issues: Issues, name: str):
    """Validates the name (which are used as unique identifiers in Croissant)."""
    if not isinstance(name, str):
        issues.add_error(f"The identifier should be a string. Got: {type(name)}.")
    if len(name) > _MAX_ID_LENGTH:
        issues.add_error(
            f'The identifier "{name}" is too long (>{_MAX_ID_LENGTH} characters).'
        )
    regex = re.compile(rf"^{ID_REGEX}$")
    if not regex.match(name):
        issues.add_error(f'The identifier "{name}" contains forbidden characters.')
    return name


def there_exists_at_least_one_property(node: Node, possible_properties: list[str]):
    """Checks for the existence of one of `possible_exclusive_properties` in `keys`."""
    for possible_property in possible_properties:
        if getattr(node, possible_property, None) is not None:
            return True
    return False
