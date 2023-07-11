"""Structure graph module.

The goal of this module is the static analysis of the JSON file. We convert the initial
JSON to a so-called "structure graph", which is a Python representation of the JSON
containing the nodes (Metadata, FileObject, etc) and the hierarchy between them. In the
process of parsing all the nodes, we also check that no information is missing and raise
issues (errors or warnings) when necessary. See the docstring of
`from_nodes_to_structure_graph` for more information.

The important functions of this module are:
- from_file_to_json             file -> JSON
- from_json_to_rdf              JSON -> RDF
- from_rdf_to_nodes             RDF -> nodes
- from_nodes_to_structure_graph nodes -> structure graph
"""

import json
from typing import Any

from etils import epath
from ml_croissant._src.core import constants
from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.nodes import (
    Field,
    FileObject,
    FileSet,
    Metadata,
    RecordSet,
    Source,
)
from ml_croissant._src.structure_graph.nodes.source import parse_reference
import networkx as nx
import rdflib
from rdflib import namespace
from rdflib import term

Json = dict[str, Any]

NodeType = type[Field | FileObject | FileSet | Metadata | Node | RecordSet]


def from_file_to_json(filepath: epath.PathLike) -> tuple[epath.Path, Json]:
    """Loads the file as a JSON.

    Args:
        filepath: The path to the file as a str or a path. The path can be absolute or
            relative.

    Returns:
        A tuple with the absolute path to the file and the JSON.
    """
    filepath = epath.Path(filepath).expanduser().resolve()
    if not filepath.exists():
        raise ValueError(f"File {filepath} does not exist.")
    with filepath.open() as f:
        return filepath, json.load(f)


def from_json_to_rdf(data: Json) -> tuple[namespace.NamespaceManager, rdflib.Graph]:
    """Converts the JSON to an RDF graph with expanded JSON-LD attributes using RDFLib.

    We use RDFLib instead of reinventing a JSON-LD parser. This may be more cumbersome
    short-term, but will prove handy long-term, when we integrate more advanced feature
    of RDF/JSON-LD, or other parsers (e.g., YAML-LD).

    We prefer the RDF graph representation over the JSON-LD representation because the
    former is easier to traverse the graph than the JSON.

    Args:
        data: The JSON dict.

    Returns:
        A tuple with the RDF namespace manager (see:
            https://rdflib.readthedocs.io/en/stable/namespaces_and_bindings.html) and
            the RDF graph.
    """
    graph = rdflib.Graph()
    graph.parse(
        data=data,
        format="json-ld",
    )
    ns = graph.namespace_manager
    return ns, graph


def _parse_node_params(
    issues: Issues, rdf_graph: rdflib.Graph, bnode: term.BNode, no_filter: bool = False
) -> Json:
    """Recursively parses all information from a node to Croissant."""
    # TODO(marcenacp): Type node params.
    node_params = {}
    for _, _predicate, _object in rdf_graph.triples((bnode, None, None)):
        if _predicate == constants.ML_COMMONS_SUB_FIELD:
            node_params["has_sub_fields"] = True
        elif no_filter or _predicate in constants.TO_CROISSANT:
            croissant_key = constants.TO_CROISSANT[_predicate]
            if isinstance(_object, term.Literal):
                node_params[croissant_key] = str(_object)
            elif isinstance(_object, term.BNode):
                current_node_params = _parse_node_params(
                    issues, rdf_graph, _object, no_filter=True
                )
                if croissant_key not in node_params:
                    node_params[croissant_key] = [current_node_params]
                elif isinstance(node_params[croissant_key], list):
                    node_params[croissant_key].append(current_node_params)
                else:
                    raise ValueError("Recursive calls should always be lists.")
            else:
                raise ValueError("Objects are either Bnodes or Literals.")
    # Parse `source`.
    if (source := node_params.get("source")) is not None:
        node_params["source"] = Source.from_json_ld(issues, source)
    # Parse `references`.
    if (references := node_params.get("references")) is not None:
        node_params["references"] = Source.from_json_ld(issues, references)
    # Parse `contained_in`.
    if (contained_in := node_params.get("contained_in")) is not None:
        if isinstance(contained_in, str):
            node_params["contained_in"] = parse_reference(issues, contained_in)
        else:
            node_params["contained_in"] = (
                parse_reference(issues, reference)[0] for reference in contained_in
            )
    return node_params


def _parse_node(
    issues: Issues,
    rdf_graph: rdflib.Graph,
    bnode: term.BNode,
    expected_types: tuple[str, ...],
    graph: nx.MultiDiGraph(),
    parents: tuple[Node, ...],
) -> Node | None:
    node_type = rdf_graph.value(bnode, constants.RDF_TYPE)
    if node_type is None:
        issues.add_error('The node doesn\'t define the "@type" property.')
        return None
    node_type = term.URIRef(node_type)
    rdf_to_croissant = {
        constants.SCHEMA_ORG_DATASET: Metadata,
        constants.SCHEMA_ORG_FILE_OBJECT: FileObject,
        constants.SCHEMA_ORG_FILE_SET: FileSet,
        constants.ML_COMMONS_FIELD: Field,
        constants.ML_COMMONS_RECORD_SET: RecordSet,
    }
    if node_type not in rdf_to_croissant:
        # TODO(marcenacp): Propagate the context here.
        issues.add_error(
            'Node should have an attribute `"@type" in'
            f" {list(rdf_to_croissant.keys())}. Got {node_type} instead."
        )
        return None
    node_cls = rdf_to_croissant[node_type]
    if node_type not in expected_types:
        issues.add_error(
            f'Node should have an attribute `"@type" in {expected_types}. Got'
            f" {node_type} instead."
        )
        return None
    node_params = _parse_node_params(issues, rdf_graph, bnode)
    return node_cls(
        issues=issues, bnode=bnode, graph=graph, parents=parents, **node_params
    )


def _parse_children(
    issues: Issues,
    rdf_graph: rdflib.Graph,
    expected_property: str,
    expected_types: tuple[str, ...],
    graph: nx.MultiDiGraph,
    parents: tuple[Node, ...],
) -> list[Node]:
    children: list[Node] = []
    if len(parents) == 0:
        raise ValueError("This function should not be used on metadata.")
    parent = parents[-1]
    for _, _, _object in rdf_graph.triples((parent.bnode, expected_property, None)):
        node = _parse_node(issues, rdf_graph, _object, expected_types, graph, parents)
        if node is not None:
            children.append(node)
    return children


def from_rdf_to_nodes(issues: Issues, rdf_graph: rdflib.Graph) -> nx.MultiDiGraph:
    """Converts the RDF graph to a list of Python-readable nodes.

    Args:
        issues: The issues to populate in case of problem.
        graph: The RDF graph with expanded properties.

    Returns:
        The structure graph with only nodes and without edges.
    """
    graph = nx.MultiDiGraph()
    entry_nodes = rdf_graph.subjects(
        predicate=constants.RDF_TYPE, object=constants.SCHEMA_ORG_DATASET
    )
    metadata_bnode = next(entry_nodes, None)
    if not metadata_bnode:
        return graph
    metadata = _parse_node(
        issues=issues,
        rdf_graph=rdf_graph,
        bnode=metadata_bnode,
        expected_types=(constants.SCHEMA_ORG_DATASET,),
        graph=graph,
        parents=(),
    )
    if metadata is None:
        return graph
    graph.add_node(metadata)
    distributions = _parse_children(
        issues=issues,
        rdf_graph=rdf_graph,
        expected_property=constants.SCHEMA_ORG_DISTRIBUTION,
        expected_types=(
            constants.SCHEMA_ORG_FILE_OBJECT,
            constants.SCHEMA_ORG_FILE_SET,
        ),
        graph=graph,
        parents=(metadata,),
    )
    record_sets = _parse_children(
        issues=issues,
        rdf_graph=rdf_graph,
        expected_property=constants.ML_COMMONS_RECORD_SET,
        expected_types=(constants.ML_COMMONS_RECORD_SET,),
        graph=graph,
        parents=(metadata,),
    )

    for distribution in distributions:
        graph.add_node(distribution)
    for record_set in record_sets:
        graph.add_node(record_set)
    for record_set in record_sets:
        fields = _parse_children(
            issues=issues,
            rdf_graph=rdf_graph,
            expected_property=constants.ML_COMMONS_FIELD,
            expected_types=(constants.ML_COMMONS_FIELD,),
            graph=graph,
            parents=(metadata, record_set),
        )
        for field in fields:
            graph.add_node(field)
            sub_fields = _parse_children(
                issues=issues,
                rdf_graph=rdf_graph,
                expected_property=constants.ML_COMMONS_SUB_FIELD,
                expected_types=(constants.ML_COMMONS_FIELD,),
                graph=graph,
                parents=(metadata, record_set, field),
            )
            for sub_field in sub_fields:
                graph.add_node(sub_field)
    node: Node
    for node in graph.nodes:
        node.check()
    return graph


def get_entry_nodes(graph: nx.MultiDiGraph) -> list[Node]:
    """Retrieves the entry nodes (without predecessors) in a graph."""
    entry_nodes: list[Node] = []
    for node, indegree in graph.in_degree(graph.nodes()):
        if indegree == 0:
            entry_nodes.append(node)
    # Fields should usually not be entry nodes, except if they have subFields. So we
    # check for this:
    for node in entry_nodes:
        if isinstance(node, Field) and not node.has_sub_fields and not node.data:
            node.add_error(
                f'Node "{node.uid}" is a field and has no source. Please, use'
                f" {constants.ML_COMMONS_SOURCE} to specify the source."
            )
    return entry_nodes


def _check_no_duplicate(graph: nx.MultiDiGraph) -> dict[str, Node]:
    """Checks that no node has duplicated UID and returns the mapping `uid`->`Node`."""
    uid_to_node: dict[str, Node] = {}
    node: Node
    for node in graph.nodes:
        if node.uid in uid_to_node:
            node.add_error(
                f"Duplicate nodes with the same identifier: {uid_to_node[node.uid].uid}"
            )
        uid_to_node[node.uid] = node
    return uid_to_node


def _add_node_as_entry_node(graph: nx.MultiDiGraph, node: Node):
    """Add `node` as the entry node of the graph by updating `graph` in place."""
    graph.add_node(node, parent=None)
    entry_nodes = get_entry_nodes(graph)
    for entry_node in entry_nodes:
        if isinstance(node, (FileObject, FileSet)):
            graph.add_edge(entry_node, node)


def _add_edge(
    issues: Issues,
    graph: nx.MultiDiGraph,
    uid_to_node: dict[str, Node],
    uid: str,
    node: Node,
    expected_types: NodeType | tuple[NodeType, ...],
):
    """Adds an edge in the structure graph."""
    if uid not in uid_to_node:
        issues.add_error(
            f'There is a reference to node named "{uid}" in node "{node.uid}", but this'
            " node doesn't exist."
        )
        return
    if not isinstance(uid_to_node[uid], expected_types):
        issues.add_error(
            f'There is a reference to node named "{uid}" in node "{node.uid}", but this'
            f" node doesn't have the expected type: {expected_types}."
        )
        return
    graph.add_edge(uid_to_node[uid], node)


def _concatenate_uid(source: tuple[str]) -> str:
    return "/".join(source)


def from_nodes_to_structure_graph(
    issues: Issues, graph: nx.MultiDiGraph
) -> tuple[Metadata | None, nx.MultiDiGraph]:
    """Populates the structure graph from the list of node.

    In the structure graph:
    - Nodes are Metadata, FileObjects, FileSets and Fields.
    - Nodes must have a parent property, which is their direct parent in the Croissant
      JSON.
    - Nodes can have predecessor which is the source where data comes from. I.e., for
      a field, the source of the data or a join, etc.

    Args:
        issues: The issues to populate in case of problem.
        nodes: The list of Python nodes.
        parents: The list of nodes

    Returns:
        The structure graph with the proper hierarchy.
    """
    uid_to_node = _check_no_duplicate(graph)
    metadata = None
    node: Node
    for node in graph.nodes:
        # Metadata
        if isinstance(node, Metadata):
            metadata = node
            continue
        if not node.parents:
            raise ValueError("Non metadata nodes always have at least one parent.")
        # Distribution
        if isinstance(node, (FileObject, FileSet)) and node.contained_in:
            for uid in node.contained_in:
                _add_edge(issues, graph, uid_to_node, uid, node, (FileObject, FileSet))
        # Fields
        elif isinstance(node, Field):
            references = []
            if node.source:
                references.append(node.source.reference)
            if node.references:
                references.append(node.references.reference)
            # The source can be embedded with in-line data in the parent record set.
            if node.data:
                parent = node.parents[-1]
                _add_edge(issues, graph, uid_to_node, parent.uid, node, RecordSet)
            for reference in references:
                # The source can be either another field...
                if (uid := _concatenate_uid(reference)) in uid_to_node:
                    # Record sets are not valid parents here.
                    # The case can arise when a Field references a record set to have a
                    # machine-readable explanation of the field (see datasets/titanic
                    # for example).
                    if not isinstance(uid_to_node[uid], RecordSet):
                        _add_edge(issues, graph, uid_to_node, uid, node, Node)
                # ...or the source can be a distribution (e.g., column of a CSV file).
                elif reference and (uid := reference[0]) in uid_to_node:
                    if not isinstance(uid_to_node[uid], RecordSet):
                        _add_edge(
                            issues, graph, uid_to_node, uid, node, (FileObject, FileSet)
                        )
                else:
                    issues.add_error(
                        "Source refers to an unknown node"
                        f' "{_concatenate_uid(reference)}".'
                    )
    # `Metadata` are used as the entry node.
    if metadata is None:
        issues.add_error(
            "No metadata is defined in the dataset. Make sure you defined a node with"
            f" @type={constants.SCHEMA_ORG_DATASET}."
        )
        return metadata, graph
    _add_node_as_entry_node(graph, metadata)
    return metadata, graph


def check_structure_graph(issues: Issues, graph: nx.MultiDiGraph):
    """Checks the integrity of the structure graph.

    The rules are the following:
    - The graph is directed.
    - ALl fields have a data type: either specify directly, or on a parent.

    Args:
        issues: The issues to populate in case of problem.
        graph: The structure graph to be checked.
    """
    # Check that the graph is directed.
    if not graph.is_directed():
        issues.add_error("Structure graph is not directed.")
    fields = [node for node in graph.nodes if isinstance(node, Field)]
    # Check all fields have a data type: either on the field, on a parent.
    for field in fields:
        field.data_type
