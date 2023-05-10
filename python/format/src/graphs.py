import dataclasses
from collections.abc import Mapping
import json
from typing import Any, List, Set

import networkx as nx
import rdflib
from rdflib.extras import external_graph_libs

from format.src import constants
from format.src import errors

# Edges are always RDF triples, because we use `graph.edges(node, keys=True) -> (u, v, key)`.
Edges = [Any, Any, Any]


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
    issues: errors.Issues
    graph: nx.MultiDiGraph
    node: rdflib.term.BNode
    properties: Mapping[str, Any] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        self.populate_properties()

    @property
    def _edges_from_node(self):
        return self.graph.edges(self.node, keys=True)

    @property
    def id(self):
        return self.__getitem__(constants.SCHEMA_ORG_NAME)

    def children_nodes(self, expected_property: str) -> list["Node"]:
        """Finds all children objects/nodes."""
        return [
            Node(issues=self.issues, graph=self.graph, node=value)
            for _, value, property in self._edges_from_node
            if isinstance(value, rdflib.term.BNode) and expected_property == property
        ]

    def populate_properties(self):
        for _, value, property in self._edges_from_node:
            if not isinstance(value, rdflib.term.BNode):
                self.properties[property] = value

    def assert_has_type(self, expected_type: str):
        """Checks for the presence of `"@type": expected_type` in edges."""
        node_type = self.properties[constants.RDF_TYPE]
        if node_type != expected_type:
            error = f'Node should have an attribute `"@type": "{expected_type}"`. Found `"@type": "{node_type}"`.'
            self.issues.add_error(error)

    def assert_has_types(self, expected_types: list[str]):
        """Checks for the presence of `"@type": expected_types` in edges."""
        node_type = self.properties[constants.RDF_TYPE]
        if all(node_type != expected_type for expected_type in expected_types):
            error = f'Node should have an attribute `"@type" in "{expected_types}"`. Found `"@type": "{node_type}"`.'
            self.issues.add_error(error)

    def assert_has_mandatory_properties(self, mandatory_properties: list[str]):
        """Checks a node in the graph for existing properties with constraints.

        Args:
            mandatory_properties: A list of mandatory properties for the current node. If the node doesn't have one, it triggers an error.
        """
        for mandatory_property in mandatory_properties:
            if mandatory_property not in self.properties:
                error = (
                    f'Property "{mandatory_property}" is mandatory, but does not exist.'
                )
                self.issues.add_error(error)

    def assert_has_optional_properties(self, optional_properties: list[str]):
        """Checks a node in the graph for existing properties with constraints.

        Args:
            optional_properties: A list of optional properties for the current node. If the node doesn't have one, it triggers a warning.
        """
        for optional_property in optional_properties:
            if optional_property not in self.properties:
                error = f'Property "{optional_property}" is recommended, but does not exist.'
                self.issues.add_warning(error)

    def assert_has_exclusive_properties(self, exclusive_properties: list[list[str]]):
        """Checks a node in the graph for existing properties with constraints.

        Args:
            exclusive_properties: A list of list of exclusive properties: the current node should have at least one.
        """
        for possible_exclusive_properties in exclusive_properties:
            if not _there_exists_at_least_one_property(
                self.properties, possible_exclusive_properties
            ):
                error = f"At least one of these properties should be defined: {possible_exclusive_properties}."
                self.issues.add_error(error)

    def __repr__(self):
        """String representation of the node for debugging purposes."""
        return f"Node(properties={json.dumps(self.properties)})"

    def __getitem__(self, name: Any):
        """Magic method to be able to write `node[property_name]` to access its property."""
        if name in self.properties:
            return self.properties[name]
        error = f'Tried to access property "{name}", but it does not exist.'
        self.issues.add_error(error)
        return None

    def __iter__(self):
        """Magic method to be able to write `property_name in node`."""
        for property in self.properties:
            yield property

def load_rdf_graph(dict_dataset: dict) -> nx.MultiDiGraph:
    """Parses RDF graph with NetworkX from a dict."""
    graph = rdflib.Graph()
    graph.parse(
        data=dict_dataset,
        format="json-ld",
    )
    return external_graph_libs.rdflib_to_networkx_multidigraph(graph)


def _there_exists_at_least_one_property(keys: Set[str], possible_properties: List[str]):
    """Checks for the existence of one of `possible_exclusive_properties` in `keys`."""
    for possible_property in possible_properties:
        if possible_property in keys:
            return True
    return False


def _find_entry_object(
    issues: errors.Issues, graph: nx.MultiDiGraph
) -> rdflib.term.BNode:
    """Finds the source entry node without any parent."""
    sources = [
        node
        for node, indegree in graph.in_degree(graph.nodes())
        if indegree == 0 and isinstance(node, rdflib.term.BNode)
    ]
    if len(sources) != 1:
        issues.add_error(f"Trying to define more than one dataset in the file.")
    return sources[0]


def check_metadata(
    issues: errors.Issues,
    metadata: Node,
):
    """Populates issues on the Metadata node."""
    dataset_id = metadata.id
    with issues.context(f"dataset({dataset_id})"):
        metadata.assert_has_type(constants.SCHEMA_ORG_DATASET)
        metadata.assert_has_mandatory_properties(
            [
                constants.SCHEMA_ORG_NAME,
                constants.SCHEMA_ORG_URL,
            ]
        )
        metadata.assert_has_optional_properties(
            [
                constants.SCHEMA_ORG_CITATION,
                constants.SCHEMA_ORG_LICENSE,
                constants.SCHEMA_ORG_DESCRIPTION,
            ]
        )


def check_distribution(
    issues: errors.Issues,
    distribution: Node,
    metadata: Node,
):
    """Populates issues on the Distribution nodes."""
    dataset_id = metadata.id
    distribution_id = distribution.id
    with issues.context(f"dataset({dataset_id}) > distribution({distribution_id})"):
        distribution.assert_has_types([constants.SCHEMA_ORG_FILE_OBJECT, constants.SCHEMA_ORG_FILE_SET])
        is_file_set = distribution[constants.RDF_TYPE] == constants.SCHEMA_ORG_FILE_SET
        if is_file_set:
            distribution.assert_has_mandatory_properties(
                [
                    constants.ML_COMMONS_INCLUDES,
                    constants.SCHEMA_ORG_ENCODING_FORMAT,
                ]
            )
        else:
            distribution.assert_has_mandatory_properties(
                [
                    constants.SCHEMA_ORG_CONTENT_URL,
                    constants.SCHEMA_ORG_ENCODING_FORMAT,
                ]
            )
        is_root_distribution = constants.SCHEMA_ORG_CONTAINED_IN not in distribution
        if is_root_distribution:
            distribution.assert_has_optional_properties(
                [
                    constants.SCHEMA_ORG_CONTENT_SIZE,
                ]
            )
            distribution.assert_has_exclusive_properties(
                [[constants.SCHEMA_ORG_MD5, constants.SCHEMA_ORG_SHA256]]
            )


def check_record_set(
    issues: errors.Issues,
    record_set: Node,
    metadata: Node,
):
    """Populates issues on the RecordSet nodes."""
    dataset_id = metadata.id
    record_set_id = record_set.id
    with issues.context(f"dataset({dataset_id}) > recordSet({record_set_id})"):
        record_set.assert_has_type(constants.ML_COMMONS_RECORD_SET)
        record_set.assert_has_mandatory_properties(
            [
                constants.SCHEMA_ORG_NAME,
            ]
        )
        record_set.assert_has_optional_properties(
            [
                constants.SCHEMA_ORG_DESCRIPTION,
            ]
        )
        fields = record_set.children_nodes(constants.ML_COMMONS_FIELD)
        if len(fields) == 0:
            issues.add_error("The node doesn't define any field.")
        for field in fields:
            with issues.context(
                f"dataset({dataset_id}) > recordSet({record_set_id}) > field({field.id})"
            ):
                field.assert_has_type(constants.ML_COMMONS_FIELD)
                field.assert_has_mandatory_properties(
                    [
                        constants.ML_COMMONS_DATA_TYPE,
                        constants.SCHEMA_ORG_NAME,
                    ]
                )
                field.assert_has_optional_properties(
                    [
                        constants.SCHEMA_ORG_DESCRIPTION,
                    ]
                )


def check_graph(issues: errors.Issues, graph: nx.MultiDiGraph):
    """Validates the graph and populates issues with errors/warnings.

    We first build a NetworkX graph where edges are subject->object with the attribute `property`.

    Subject/object/property are RDF triples:
        - `subject`is an ID instanciated by RDFLib.
        - `property` (aka predicate) denotes the relationship (e.g., `https://schema.org/description`).
        - `object` is either the value (e.g., the description) or another `subject`.

    Refer to https://www.w3.org/TR/rdf-concepts to learn more.

    Args:
        issues: the issues that will be modified in-place.
        graph: The NetworkX RDF graph to validate.
    """
    source = _find_entry_object(issues, graph)
    metadata = Node(issues=issues, graph=graph, node=source)
    check_metadata(issues, metadata)

    distributions = metadata.children_nodes(constants.SCHEMA_ORG_DISTRIBUTION)
    for distribution in distributions:
        check_distribution(issues, distribution, metadata)

    record_sets = metadata.children_nodes(constants.ML_COMMONS_RECORD_SET)
    for record_set in record_sets:
        check_record_set(issues, record_set, metadata)
