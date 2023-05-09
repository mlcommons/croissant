from typing import Any, List, Set

import networkx as nx
import rdflib
from rdflib.extras import external_graph_libs

from format.src import constants
from format.src import errors

# Edges are always RDF triples, because we use `graph.edges(node, keys=True) -> (u, v, key)`.
Edges = [Any, Any, Any]


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


def _check_node_has_properties(
    issues: errors.Issues,
    edges: Edges,
    mandatory_properties: List[str] = [],
    exclusive_properties: List[List[str]] = [],
    optional_properties: List[str] = [],
):
    """Checks a node in the graph for existing properties with constraints.

    Args:
        issues: The issues that will be modified in-place.
        edges: Edges of the current node.
        mandatory_properties: A list of mandatory properties for the current node. If the node doesn't have one, it triggers an error.
        exclusive_properties: A list of list of exclusive properties: the current node should have at least one.
        optional_properties: A list of optional properties for the current node. If the node doesn't have one, it triggers a warning.
    """
    properties = set()
    for _, _, property in edges:
        properties.add(property)
    for property in mandatory_properties:
        if property not in properties:
            error = f'Property "{property}" is mandatory, but does not exist. Existing properties: {properties}.'
            issues.add_error(error)
    for property in optional_properties:
        if property not in properties:
            error = f'Property "{property}" is recommended, but does not exist. Existing properties: {properties}.'
            issues.add_warning(error)
    for possible_exclusive_properties in exclusive_properties:
        if not _there_exists_at_least_one_property(
            properties, possible_exclusive_properties
        ):
            error = f"At least one of these properties should be defined: {possible_exclusive_properties}. Existing properties: {properties}."
            issues.add_error(error)


def _find_children_objects(edges: Edges, property: rdflib.term.URIRef):
    """Finds all children objects/nodes."""
    return [
        _object
        for _, _object, _property in edges
        if isinstance(_object, rdflib.term.BNode) and _property == property
    ]


def _find_single_object_by_property(
    issues: errors.Issues, edges: Edges, property: rdflib.term.URIRef
):
    """Finds value where `[property]: value` in edges."""
    possible_objects = [
        _object for _, _object, _property in edges if _property == property
    ]
    if len(possible_objects) != 1:
        issues.add_error(
            f'Property "{property}" is mandatory, but does not exist. Existing properties: {edges}.'
        )
    return possible_objects[0]


def _find_name(issues: errors.Issues, edges: Edges):
    return _find_single_object_by_property(issues, edges, constants.SCHEMA_ORG_NAME)


def _check_node_has_type(
    issues: errors.Issues, edges: Edges, _type: rdflib.term.URIRef
):
    """Checks for the presence of `"@type": _type` in edges."""
    for _, _object, _property in edges:
        if _property == constants.RDF_TYPE:
            if _object != _type:
                issues.add_error(
                    f'Node should have an attribute `"@type": "{_type}"`. Found `"@type": "{_object}"`.'
                )
            return
    issues.add_error(f'Node should have an attribute `"@type": "{_type}"`.')


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
    edges: Edges,
    dataset_name: str,
):
    """Populates issues on the Metadata node."""
    with issues.context(f"dataset({dataset_name})"):
        _check_node_has_type(issues, edges, constants.SCHEMA_ORG_DATASET)
        _check_node_has_properties(
            issues,
            edges,
            mandatory_properties=[
                constants.SCHEMA_ORG_CITATION,
                constants.SCHEMA_ORG_LICENSE,
                constants.SCHEMA_ORG_NAME,
                constants.SCHEMA_ORG_URL,
            ],
            optional_properties=[constants.SCHEMA_ORG_DESCRIPTION],
        )


def check_distribution(
    issues: errors.Issues,
    graph: nx.MultiDiGraph,
    node: rdflib.term.BNode,
    dataset_name: str,
):
    """Populates issues on the Distribution nodes."""
    edges_from_node = graph.edges(node, keys=True)
    distribution_name = _find_name(issues, edges_from_node)
    with issues.context(f"dataset({dataset_name}) > distribution({distribution_name})"):
        _check_node_has_type(issues, edges_from_node, constants.SCHEMA_ORG_FILE_OBJECT)
        _check_node_has_properties(
            issues,
            edges_from_node,
            mandatory_properties=[
                constants.SCHEMA_ORG_CONTENT_SIZE,
                constants.SCHEMA_ORG_CONTENT_URL,
                constants.SCHEMA_ORG_ENCODING_FORMAT,
            ],
            exclusive_properties=[
                [constants.SCHEMA_ORG_MD5, constants.SCHEMA_ORG_SHA256]
            ],
        )


def check_record_set(
    issues: errors.Issues,
    graph: nx.MultiDiGraph,
    node: rdflib.term.BNode,
    dataset_name: str,
):
    """Populates issues on the RecordSet nodes."""
    edges_from_node = graph.edges(node, keys=True)
    record_set_name = _find_name(issues, edges_from_node)
    with issues.context(f"dataset({dataset_name}) > recordSet({record_set_name})"):
        _check_node_has_type(issues, edges_from_node, constants.ML_COMMONS_RECORD_SET)
        _check_node_has_properties(
            issues,
            edges_from_node,
            mandatory_properties=[
                constants.ML_COMMONS_FIELD,
                constants.SCHEMA_ORG_NAME,
            ],
            optional_properties=[
                constants.SCHEMA_ORG_DESCRIPTION,
            ],
        )
        fields = _find_children_objects(edges_from_node, constants.ML_COMMONS_FIELD)
        if len(fields) == 0:
            issues.add_error("The node doesn't define any field.")
        for field in fields:
            edges_from_node = graph.edges(field, keys=True)
            field_name = _find_name(issues, edges_from_node)
            with issues.context(
                f"dataset({dataset_name}) > recordSet({record_set_name}) > field({field_name})"
            ):
                _check_node_has_type(
                    issues, edges_from_node, constants.ML_COMMONS_FIELD
                )
                _check_node_has_properties(
                    issues,
                    edges_from_node,
                    mandatory_properties=[
                        constants.ML_COMMONS_DATA_TYPE,
                        constants.SCHEMA_ORG_NAME,
                    ],
                    optional_properties=[
                        constants.SCHEMA_ORG_DESCRIPTION,
                    ],
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
    edges_from_source = graph.edges(source, keys=True)
    dataset_name = _find_name(issues, edges_from_source)
    check_metadata(issues, edges_from_source, dataset_name)

    distributions = _find_children_objects(
        edges_from_source, constants.SCHEMA_ORG_DISTRIBUTION
    )
    for distribution in distributions:
        check_distribution(issues, graph, distribution, dataset_name)

    record_sets = _find_children_objects(
        edges_from_source, constants.ML_COMMONS_RECORD_SET
    )
    for record_set in record_sets:
        check_record_set(issues, graph, record_set, dataset_name)
