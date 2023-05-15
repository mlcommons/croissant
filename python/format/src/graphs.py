"""graphs module."""

import networkx as nx
import rdflib
from rdflib.extras import external_graph_libs

from format.src import constants
from format.src.errors import Issues
from format.src.nodes import Node


def load_rdf_graph(dict_dataset: dict) -> nx.MultiDiGraph:
    """Parses RDF graph with NetworkX from a dict."""
    graph = rdflib.Graph()
    graph.parse(
        data=dict_dataset,
        format="json-ld",
    )
    return external_graph_libs.rdflib_to_networkx_multidigraph(graph)


def _find_entry_object(issues: Issues, graph: nx.MultiDiGraph) -> rdflib.term.BNode:
    """Finds the source entry node without any parent."""
    sources = [
        node
        for node, indegree in graph.in_degree(graph.nodes())
        if indegree == 0 and isinstance(node, rdflib.term.BNode)
    ]
    if len(sources) != 1:
        issues.add_error("Trying to define more than one dataset in the file.")
    return sources[0]


def check_rdf_graph(issues: Issues, graph: nx.MultiDiGraph) -> list[Node]:
    """Validates the graph and populates issues with errors/warnings.

    We first build a NetworkX graph where edges are subject->object with the attribute
    `property`.

    Subject/object/property are RDF triples:
        - `subject`is an ID instanciated by RDFLib.
        - `property` (aka predicate) denotes the relationship (e.g.,
        `https://schema.org/description`).
        - `object` is either the value (e.g., the description) or another `subject`.

    Refer to https://www.w3.org/TR/rdf-concepts to learn more.

    Args:
        issues: the issues that will be modified in-place.
        graph: The NetworkX RDF graph to validate.
    """
    # Check RDF properties in nodes
    source = _find_entry_object(issues, graph)
    metadata = Node.from_rdf_graph(issues, graph, source, None)
    nodes: list[Node] = [metadata]
    dataset_name = metadata.name
    with issues.context(dataset_name=dataset_name, distribution_name=""):
        distributions = metadata.children_nodes(constants.SCHEMA_ORG_DISTRIBUTION)
        nodes += distributions
        record_sets = metadata.children_nodes(constants.ML_COMMONS_RECORD_SET)
        nodes += record_sets
        for record_set in record_sets:
            with issues.context(
                dataset_name=dataset_name,
                record_set_name=record_set.name,
                field_name="",
            ):
                fields = record_set.children_nodes(constants.ML_COMMONS_FIELD)
                nodes += fields
                if len(fields) == 0:
                    issues.add_error("The node doesn't define any field.")
                for field in fields:
                    sub_fields = field.children_nodes(constants.ML_COMMONS_SUB_FIELD)
                    nodes += sub_fields
    return nodes
