import dataclasses
import re

import networkx as nx
import rdflib

from format.src import constants
from format.src.errors import Issues

_MAX_ID_LENGTH = 255
_ID_REGEX = "[a-zA-Z0-9\-_]+"


@dataclasses.dataclass(frozen=True)
class Node:
    """Resource node in Croissant.

    When performing all operations, `self.issues` are populated when issues are encountered.

    Usage:

    ```python
    node = Node(issues=issues, graph=graph, node=source)

    # Can access a property of the node:
    citation = node["https://schema.org/citation"]

    # Can check a property exists:
    has_citation = "https://schema.org/citation" in node

    # Can assert features on the node. E.g.:
    node.assert_has_exclusive_properties([[""https://schema.org/sha256"", "https://schema.org/md5"]])
    ```
    """

    issues: Issues
    graph: nx.MultiDiGraph
    node: rdflib.term.BNode
    name: str = ""

    def __post_init__(self):
        self.assert_has_mandatory_properties("name")
        self.validate_name(self.name)

    @classmethod
    def from_rdf_graph(
        cls: "Node",
        issues: Issues,
        graph: nx.MultiDiGraph,
        node: rdflib.term.BNode,
    ) -> "Node":
        properties = {}
        for _, value, property in graph.edges(node, keys=True):
            if isinstance(value, rdflib.term.BNode):
                continue

            # Normalize values to strings.
            if isinstance(value, rdflib.term.Literal):
                value = str(value)

            # Normalize properties to Croissant values if it exists.
            property = constants.TO_CROISSANT.get(property, property)

            # Add `property` to existing properties.
            if property not in properties:
                properties[property] = value
            elif isinstance(properties[property], tuple):
                # Use tuple, because we need immutable types in order
                # for the objects to be hashable and used by NetworkX.
                properties[property] = properties[property] + (value,)
            else:
                # In the loop, we just found out that there are several values for the
                # same property. `self.properties[property]` should be transformed to a tuple.
                properties[property] = (properties[property], value)

        name = properties.get("name")
        rdf_type = properties.get(constants.RDF_TYPE)
        expected_types = [
            constants.SCHEMA_ORG_DATASET,
            constants.SCHEMA_ORG_FILE_OBJECT,
            constants.SCHEMA_ORG_FILE_SET,
            constants.ML_COMMONS_RECORD_SET,
            constants.ML_COMMONS_FIELD,
            constants.ML_COMMONS_SUB_FIELD,
        ]
        if rdf_type not in expected_types:
            issues.add_error(
                f'Node should have an attribute `"@type" in "{expected_types}"`.'
            )
        if rdf_type == constants.SCHEMA_ORG_DATASET:
            with issues.context(dataset_name=name):
                return Metadata(
                    issues=issues,
                    graph=graph,
                    node=node,
                    citation=properties.get("citation"),
                    description=properties.get("description"),
                    license=properties.get("license"),
                    name=name,
                    url=properties.get("url"),
                )
        elif rdf_type == constants.SCHEMA_ORG_FILE_OBJECT:
            with issues.context(distribution_name=name):
                return FileObject(
                    issues=issues,
                    graph=graph,
                    node=node,
                    content_url=properties.get("content_url"),
                    description=properties.get("description"),
                    encoding_format=properties.get("encoding_format"),
                    md5=properties.get("md5"),
                    name=name,
                    sha256=properties.get("sha256"),
                )
        elif rdf_type == constants.SCHEMA_ORG_FILE_SET:
            with issues.context(distribution_name=name):
                return FileSet(
                    issues=issues,
                    graph=graph,
                    node=node,
                    contained_in=properties.get("contained_in"),
                    description=properties.get("description"),
                    includes=properties.get("includes"),
                    encoding_format=properties.get("encoding_format"),
                    name=name,
                )
        elif rdf_type == constants.ML_COMMONS_RECORD_SET:
            with issues.context(record_set_name=name):
                return RecordSet(
                    issues=issues,
                    graph=graph,
                    node=node,
                    description=properties.get("description"),
                    key=properties.get("key"),
                    name=name,
                )
        elif rdf_type == constants.ML_COMMONS_FIELD:
            with issues.context(field_name=name):
                return Field(
                    issues=issues,
                    graph=graph,
                    node=node,
                    description=properties.get("description"),
                    name=name,
                    references=properties.get("references"),
                    source=properties.get("source"),
                )
        elif rdf_type == constants.ML_COMMONS_SUB_FIELD:
            with issues.context(sub_field_name=name):
                return SubField(
                    issues=issues,
                    graph=graph,
                    node=node,
                    description=properties.get("description"),
                    name=name,
                    references=properties.get("references"),
                    source=properties.get("source"),
                )
        return Node(
            issues=issues,
            graph=graph,
            node=node,
            name=name,
        )

    @property
    def _edges_from_node(self):
        return self.graph.edges(self.node, keys=True)

    @property
    def id(self):
        node_id = str(self.name)
        # _check_id(self.issues, node_id)  # TODO(marcenacp): move these checks to __post_init__.
        return node_id

    @property
    def sources(self) -> list[tuple[str]]:
        # source can be contained either in `source` or in `contained_in`.
        if hasattr(self, "source") and isinstance(self.source, Source):
            return (self.source,)
        if hasattr(self, "contained_in"):
            return tuple(
                source for source in self.contained_in if isinstance(source, Source)
            )
        return ()

    def children_nodes(self, expected_property: str) -> list["Node"]:
        """Finds all children objects/nodes."""
        nodes = []
        for _, _object, _property in self._edges_from_node:
            if (
                isinstance(_object, rdflib.term.BNode)
                and expected_property == _property
            ):
                nodes.append(
                    Node.from_rdf_graph(
                        issues=self.issues,
                        graph=self.graph,
                        node=_object,
                    )
                )
        return nodes

    def assert_has_mandatory_properties(self, *mandatory_properties: list[str]):
        """Checks a node in the graph for existing properties with constraints.

        Args:
            mandatory_properties: A list of mandatory properties for the current node. If the node doesn't have one, it triggers an error.
        """
        for mandatory_property in mandatory_properties:
            value = getattr(self, mandatory_property)
            if not value:
                error = f'Property "{constants.FROM_CROISSANT.get(mandatory_property)}" is mandatory, but does not exist.'
                self.issues.add_error(error)

    def assert_has_optional_properties(self, *optional_properties: list[str]):
        """Checks a node in the graph for existing properties with constraints.

        Args:
            optional_properties: A list of optional properties for the current node. If the node doesn't have one, it triggers a warning.
        """
        for optional_property in optional_properties:
            value = getattr(self, optional_property)
            if not value:
                error = f'Property "{constants.FROM_CROISSANT.get(optional_property)}" is recommended, but does not exist.'
                self.issues.add_warning(error)

    def assert_has_exclusive_properties(self, *exclusive_properties: list[list[str]]):
        """Checks a node in the graph for existing properties with constraints.

        Args:
            exclusive_properties: A list of list of exclusive properties: the current node should have at least one.
        """
        for possible_exclusive_properties in exclusive_properties:
            if not _there_exists_at_least_one_property(
                self, possible_exclusive_properties
            ):
                error = f"At least one of these properties should be defined: {possible_exclusive_properties}."
                self.issues.add_error(error)

    def validate_name(self, name: str):
        if not isinstance(name, str):
            self.issues.add_error(
                f"The identifier should be a string. Got: {type(name)}."
            )
        if len(name) > _MAX_ID_LENGTH:
            self.issues.add_error(
                f'The identifier "{name}" is too long (>{_MAX_ID_LENGTH} characters).'
            )
        regex = re.compile(rf"^{_ID_REGEX}$")
        if not regex.match(name):
            self.issues.add_error(
                f'The identifier "{name}" contains forbidden characters.'
            )
        return name

    def parse_source(self, source: str) -> tuple[str]:
        source_regex = re.compile(rf"^\#\{{(?:({_ID_REGEX})\/)*({_ID_REGEX})\}}$")
        match = source_regex.match(source)
        if match is None:
            self.issues.add_error(f"Malformed source: {self.source}.")
            return ""
        groups = tuple(group for group in match.groups() if group is not None)
        for group in groups:
            self.validate_name(group)
        return groups


@dataclasses.dataclass(frozen=True)
class Source:
    apply_transform_regex: str | None = None
    data: str = ""


@dataclasses.dataclass(frozen=True)
class Metadata(Node):
    citation: str | None = None
    description: str | None = None
    license: str | None = None
    name: str = ""
    url: str = ""

    def __post_init__(self):
        self.assert_has_mandatory_properties("name", "url")
        self.assert_has_optional_properties("citation", "license")


@dataclasses.dataclass(frozen=True)
class FileObject(Node):
    content_url: str = ""
    description: str | None = None
    encoding_format: str = ""
    md5: str | None = None
    name: str = ""
    sha256: str | None = None
    source: Source | None = None

    def __post_init__(self):
        self.assert_has_mandatory_properties("content_url", "encoding_format", "name")
        if self.source is None:
            self.assert_has_optional_properties("content_url")
            self.assert_has_exclusive_properties(["md5", "sha256"])


@dataclasses.dataclass(frozen=True)
class FileSet(Node):
    contained_in: tuple[str] = ()
    description: str | None = None
    encoding_format: str = ""
    includes: str = ""
    name: str = ""

    def __post_init__(self):
        self.assert_has_mandatory_properties("includes", "encoding_format", "name")


@dataclasses.dataclass(frozen=True)
class RecordSet(Node):
    description: str | None = None
    key: str | None = None
    name: str = ""

    def __post_init__(self):
        self.assert_has_mandatory_properties("name")
        self.assert_has_optional_properties("description")


@dataclasses.dataclass(frozen=True)
class Field(Node):
    data_type: str | None = None
    description: str | None = None
    name: str = ""
    references: str | None = None
    source: Source = dataclasses.field(default_factory=Source)

    def __post_init__(self):
        self.assert_has_mandatory_properties("name")
        self.assert_has_optional_properties("description")


@dataclasses.dataclass(frozen=True)
class SubField(Field):
    pass


def _there_exists_at_least_one_property(node: Node, possible_properties: list[str]):
    """Checks for the existence of one of `possible_exclusive_properties` in `keys`."""
    for possible_property in possible_properties:
        if getattr(node, possible_property, None) is not None:
            return True
    return False
