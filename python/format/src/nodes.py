"""nodes module."""

import dataclasses
import re
from typing import Any, Mapping

import networkx as nx
import rdflib

from format.src import constants
from format.src.errors import Issues

_MAX_ID_LENGTH = 255
_ID_REGEX = "[a-zA-Z0-9\\-_]+"


@dataclasses.dataclass(frozen=True)
class Node:
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
        parent_uid: UID of the parent node if it exists. This is the parent in the
            JSON-LD structure, whereas `sources` are the parents in the resource tree.

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
    graph: nx.MultiDiGraph
    node: rdflib.term.BNode
    name: str = ""
    parent_uid: str | None = None

    def __post_init__(self):
        """Checks for `name` (common property between all nodes)."""
        self.assert_has_mandatory_properties("name")
        validate_name(self.issues, self.name)

    @classmethod
    def from_rdf_graph(
        cls: "Node",
        issues: Issues,
        graph: nx.MultiDiGraph,
        node: rdflib.term.BNode,
        parent_uid: str,
    ) -> "Node":
        """Builds a Node from the provided graph."""
        properties = _extract_properties(issues, graph, node)
        name = properties.get("name")

        # Check @type.
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

        # Return proper node in each case.
        args = [issues, graph, node, name, parent_uid]
        if rdf_type == constants.SCHEMA_ORG_DATASET:
            with issues.context(dataset_name=name):
                return Metadata(
                    *args,
                    citation=properties.get("citation"),
                    description=properties.get("description"),
                    license=properties.get("license"),
                    url=properties.get("url"),
                )
        elif rdf_type == constants.SCHEMA_ORG_FILE_OBJECT:
            with issues.context(distribution_name=name):
                return FileObject(
                    *args,
                    contained_in=properties.get("contained_in"),
                    content_url=properties.get("content_url"),
                    description=properties.get("description"),
                    encoding_format=properties.get("encoding_format"),
                    md5=properties.get("md5"),
                    sha256=properties.get("sha256"),
                )
        elif rdf_type == constants.SCHEMA_ORG_FILE_SET:
            with issues.context(distribution_name=name):
                return FileSet(
                    *args,
                    contained_in=properties.get("contained_in"),
                    description=properties.get("description"),
                    includes=properties.get("includes"),
                    encoding_format=properties.get("encoding_format"),
                )
        elif rdf_type == constants.ML_COMMONS_RECORD_SET:
            with issues.context(record_set_name=name):
                return RecordSet(
                    *args,
                    data=properties.get("data"),
                    description=properties.get("description"),
                    key=properties.get("key"),
                )
        elif rdf_type == constants.ML_COMMONS_FIELD:
            with issues.context(field_name=name):
                return Field(
                    *args,
                    data_type=properties.get("data_type"),
                    description=properties.get("description"),
                    has_sub_fields=properties.get("has_sub_fields"),
                    references=properties.get("references"),
                    source=properties.get("source"),
                )
        return Node(
            issues=issues,
            graph=graph,
            node=node,
            name=name,
            parent_uid=parent_uid,
        )

    @property
    def _edges_from_node(self):
        return self.graph.edges(self.node, keys=True)

    @property
    def uid(self):
        """Creates a UID from the name.

        For fields, the UID cannot be the name, as a dataset
        can contain two fields with the same name if they are
        in different record sets for instancd.
        """
        if isinstance(self, Field):
            # Concatenate all names except the dataset name.
            return f"{self.parent_uid}/{self.name}"
        return self.name

    def children_nodes(self, expected_property: str) -> list["Node"]:
        """Finds all children objects/nodes."""
        nodes = []
        # pylint:disable=invalid-name
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
                        parent_uid=self.uid,
                    )
                )
        if not nodes and expected_property in [
            constants.ML_COMMONS_RECORD_SET,
            constants.SCHEMA_ORG_DISTRIBUTION,
        ]:
            self.issues.add_warning(
                "The current dataset doesn't declare any node of type:"
                f' "{expected_property}"'
            )
        return nodes

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
                self.issues.add_error(error)

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
                self.issues.add_warning(error)

    def assert_has_exclusive_properties(self, *exclusive_properties: list[list[str]]):
        """Checks a node in the graph for existing properties with constraints.

        Args:
            exclusive_properties: A list of list of exclusive properties: the current
                node should have at least one.
        """
        for possible_exclusive_properties in exclusive_properties:
            if not _there_exists_at_least_one_property(
                self, possible_exclusive_properties
            ):
                error = (
                    "At least one of these properties should be defined:"
                    f" {possible_exclusive_properties}."
                )
                self.issues.add_error(error)


def validate_name(issues: Issues, name: str):
    """Validates the name (which are used as unique identifiers in Croissant)."""
    if not isinstance(name, str):
        issues.add_error(f"The identifier should be a string. Got: {type(name)}.")
    if len(name) > _MAX_ID_LENGTH:
        issues.add_error(
            f'The identifier "{name}" is too long (>{_MAX_ID_LENGTH} characters).'
        )
    regex = re.compile(rf"^{_ID_REGEX}$")
    if not regex.match(name):
        issues.add_error(f'The identifier "{name}" contains forbidden characters.')
    return name


def parse_reference(issues: Issues, source_data: str) -> tuple[str]:
    source_regex = re.compile(rf"^\#\{{({_ID_REGEX})(?:\/([^\/]+))*\}}$")
    match = source_regex.match(source_data)
    if match is None:
        issues.add_error(
            f"Malformed source data: {source_data}. The source data should be written"
            " as `#{name}` where name is valid ID."
        )
        return ""
    groups = tuple(group for group in match.groups() if group is not None)
    # Only validate the root group, because others can point to external columns
    # (like in a CSV) with fuzzy names.
    validate_name(issues, groups[0])
    return groups


@dataclasses.dataclass(frozen=True)
class Source:
    """Standardizes the usage of sources.

    Croissant accepts several manners to declare sources:

    Either as a simple reference:

    ```json
    "source": "#{name_of_the_source.name_of_the_field}"
    ```

    Or jointly with transform operations:

    ```json
    "source": {
        "data": "#{name_of_the_source}",
        "applyTransform": {
            "format": "yyyy-MM-dd HH:mm:ss.S",
            "regex": "([^\\/]*)\\.jpg",
            "separator": "|"
        }
    }
    ```
    """

    reference: tuple[str] = ()
    apply_transform_regex: str | None = None
    apply_transform_separator: str | None = None

    @classmethod
    def from_json_ld(cls, issues: Issues, field: Any) -> "Source":
        if isinstance(field, str):
            return cls(reference=parse_reference(issues, field))
        elif isinstance(field, dict):
            try:
                apply_transform = field.get("apply_transform", {})
                return cls(
                    reference=parse_reference(issues, field.get("data")),
                    apply_transform_regex=apply_transform.get("regex"),
                    apply_transform_separator=apply_transform.get("separator"),
                )
            except (IndexError, TypeError) as exception:
                issues.add_error(
                    f"Malformed `source`: {field}. Got exception: {exception}"
                )
                return cls(reference="")
        else:
            issues.add_error(f"`source` has wrong type: {type(field)} ({field})")
            return cls(reference="")

    def __bool__(self):
        """Allows to write `if not node.source` / `if node.source`"""
        return len(self.reference) > 0


@dataclasses.dataclass(frozen=True)
class Metadata(Node):
    """Nodes to describe a dataset metadata."""

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
    """Nodes to describe a dataset FileObject (distribution)."""

    content_url: str = ""
    contained_in: tuple[str] = ()
    description: str | None = None
    encoding_format: str = ""
    md5: str | None = None
    name: str = ""
    sha256: str | None = None
    source: Source | None = None

    def __post_init__(self):
        self.assert_has_mandatory_properties("content_url", "encoding_format", "name")
        if not self.contained_in:
            self.assert_has_exclusive_properties(["md5", "sha256"])


@dataclasses.dataclass(frozen=True)
class FileSet(Node):
    """Nodes to describe a dataset FileSet (distribution)."""

    contained_in: tuple[str] = ()
    description: str | None = None
    encoding_format: str = ""
    includes: str = ""
    name: str = ""

    def __post_init__(self):
        self.assert_has_mandatory_properties("includes", "encoding_format", "name")


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


@dataclasses.dataclass(frozen=True)
class Field(Node):
    """Nodes to describe a dataset Field (RecordSet)."""

    data: list[Mapping[str, Any]] | None = None
    data_type: str | None = None
    description: str | None = None
    has_sub_fields: bool | None = None
    name: str = ""
    references: Source = dataclasses.field(default_factory=Source)
    source: Source = dataclasses.field(default_factory=Source)

    def __post_init__(self):
        self.assert_has_mandatory_properties("data_type", "name")
        self.assert_has_optional_properties("description")
        # TODO(marcenacp): check that `data` has the expected form if it exists.


def _there_exists_at_least_one_property(node: Node, possible_properties: list[str]):
    """Checks for the existence of one of `possible_exclusive_properties` in `keys`."""
    for possible_property in possible_properties:
        if getattr(node, possible_property, None) is not None:
            return True
    return False


def _extract_properties(
    issues: Issues, graph: nx.MultiDiGraph, node: rdflib.term.BNode
) -> Mapping[str, Any]:
    """Extracts properties RDF->Python nodes.

    Note: we could find a better way to extract information from the RDF graph.
    """
    properties: Mapping[str, str | tuple[str]] = {}
    # pylint:disable=invalid-name
    for _, _object, _property in graph.edges(node, keys=True):
        if isinstance(_object, rdflib.term.BNode):
            # `source` needs a special treatment when it is a dict.
            if _property == constants.ML_COMMONS_SOURCE:
                source = _extract_properties(issues, graph, _object)
                properties["source"] = source
            if _property == constants.ML_COMMONS_SUB_FIELD:
                properties["has_sub_fields"] = True
            continue

        # Normalize values to strings.
        if isinstance(_object, rdflib.term.Literal):
            _object = str(_object)

        # Normalize properties to Croissant values if it exists.
        _property = constants.TO_CROISSANT.get(_property, _property)

        # Add `property` to existing properties.
        if _property not in properties:
            properties[_property] = _object
        elif isinstance(properties[_property], tuple):
            # Use tuple, because we need immutable types in order
            # for the objects to be hashable and used by NetworkX.
            properties[_property] = properties[_property] + (_object,)
        else:
            # In the loop, we just found out that there are several values for the same
            # property. `self.properties[property]` should be transformed to a tuple.
            properties[_property] = (properties[_property], _object)

    # Normalize `source`.
    if (source := properties.get("source")) is not None:
        properties["source"] = Source.from_json_ld(issues, source)
    # Normalize `references`.
    if (references := properties.get("references")) is not None:
        properties["references"] = Source.from_json_ld(issues, references)
    # Normalize `contained_in`.
    if (contained_in := properties.get("contained_in")) is not None:
        if isinstance(contained_in, str):
            properties["contained_in"] = parse_reference(issues, contained_in)
        else:
            properties["contained_in"] = (
                parse_reference(issues, reference)[0] for reference in contained_in
            )
    return properties


def concatenate_uid(source: tuple[str]) -> str:
    return "/".join(source)
