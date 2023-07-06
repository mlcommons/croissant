"""Structure graph module.

The goal of this module is the static analysis of the JSON file. We convert the initial
JSON to a so-called "structure graph", which is a Python representation of the JSON
containing the nodes (Metadata, FileObject, etc) and the hierarchy between them. In the
process of parsing all the nodes, we also check that no information is missing and raise
issues (errors or warnings) when necessary. See the docstring of
`from_nodes_to_structure_graph` for more information.

The important functions of this module are:
- from_file_to_json             file -> JSON
- from_json_to_jsonld           JSON -> JSON-LD
- from_jsonld_to_nodes          JSON-LD -> nodes
- from_nodes_to_structure_graph nodes -> structure graph
"""

from collections.abc import Mapping
import dataclasses
import json
from typing import Any

from etils import epath
from ml_croissant._src.core import constants
from ml_croissant._src.core.issues import Context, Issues
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

Json = dict[str, Any] | list["Json"]

_EXPECTED_TYPES = [
    constants.SCHEMA_ORG_DATASET,
    constants.SCHEMA_ORG_FILE_OBJECT,
    constants.SCHEMA_ORG_FILE_SET,
    constants.ML_COMMONS_RECORD_SET,
    constants.ML_COMMONS_FIELD,
    constants.ML_COMMONS_SUB_FIELD,
]


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


def from_json_to_jsonld(
    data: Json,
) -> tuple[namespace.NamespaceManager, Json]:
    """Expands JSON->JSON-LD using RDFLib.

    We use RDFLib instead of reinventing a JSON-LD parser. This may be more cumbersome
    short-term, but will prove handy long-term, when we integrate more advanced feature
    of RDF/JSON-LD, or other parsers (e.g., YAML-LD).

    Args:
        data: The JSON dict.

    Returns:
        A tuple with the RDF namespace manager (see:
            https://rdflib.readthedocs.io/en/stable/namespaces_and_bindings.html) and
            the expanded JSON-LD.
    """
    graph = rdflib.Graph()
    graph.parse(
        data=data,
        format="json-ld",
    )
    ns = graph.namespace_manager
    json_ld = graph.serialize(format="json-ld")
    json_ld = json.loads(json_ld)
    return ns, json_ld


def _get_uid(predecessors: list[Node]) -> str:
    """Concatenates the names of all predecessors to get the UID."""
    if not predecessors:
        raise ValueError(
            "This should not happen, as predecessors of a node also contain the node"
            " itself."
        )
    node = predecessors[-1]
    if isinstance(node, Metadata):
        return node.name
    names: list[str] = []
    for predecessor in predecessors:
        predecessor_name = predecessor.name
        if not isinstance(predecessor, Metadata):
            names.append(predecessor_name)
    return "/".join(names)


def _get_predecessors(
    nodes: list[Node], node: Node, parents: Mapping[str, str]
) -> list[Node]:
    """Lists predecessors in the Croissant hierarchy.

    For a field for example, the predecessors are: metadata > record set > field.
    """
    node_id = node.rdf_id
    if node_id not in parents:
        return [node]
    parent_id = parents[node_id]
    parents = [_node for _node in nodes if _node.rdf_id == parent_id]
    if not parents:
        raise ValueError(f"Node {node} has no parent {parent_id}")
    parent = parents[0]
    predecessors_of_parent = _get_predecessors(nodes, parent, parents)
    return predecessors_of_parent + [node]


def _get_context(predecessors: list[Node]) -> Context:
    """Forms the context from the predecessors."""
    params = {}
    for predecessor in predecessors:
        if isinstance(predecessor, Metadata):
            params["dataset_name"] = predecessor.name
        elif isinstance(predecessor, (FileObject, FileSet)):
            params["distribution_name"] = predecessor.name
        elif isinstance(predecessor, RecordSet):
            params["record_set_name"] = predecessor.name
        elif isinstance(predecessor, Field):
            params["field_name"] = predecessor.name
    return Context(**params)


def _get_type(node: Json) -> str | None:
    node_type = node.get("@type")
    if not (isinstance(node_type, list) and node_type):
        return None
    return rdflib.term.URIRef(node_type[0])


def _get_value(issues: Issues, json_ld: Json, value: Any):
    """Helper for _parse_node_params."""
    values = []
    for element in value:
        if "@value" in element:
            values.append(element["@value"])
        elif "@id" in element:
            # In that case, we reference another node, so we have to parse its params:
            other_id = element["@id"]
            other_node = next(
                _node for _node in json_ld if _node.get("@id") == other_id
            )
            values.append(_parse_node_params(issues, json_ld, other_node))
    # TODO(marcenacp): integrate the target type in TO_CROISSANT.
    if len(values) == 1:
        return values[0]
    return tuple(values)


def _parse_node_params(issues: Issues, json_ld: Json, node: Json) -> Json:
    """Recursively parses all information from a node to Croissant."""
    node_params = {}
    node_type = _get_type(node)
    if node_type == constants.ML_COMMONS_FIELD:
        node_params["has_sub_fields"] = str(constants.ML_COMMONS_SUB_FIELD) in node
    # Parse values.
    for key, value in node.items():
        key = rdflib.term.URIRef(key)
        if key in constants.TO_CROISSANT:
            croissant_key = constants.TO_CROISSANT[key]
            node_params[croissant_key] = _get_value(issues, json_ld, value)
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


def from_jsonld_to_nodes(
    issues: Issues, json_ld: Json
) -> tuple[list[Node], Mapping[str, str]]:
    """Converts JSON-LD to a list of Python-readable nodes.

    Args:
        issues: The issues to populate in case of problem.
        json_ld: The parsed JSON-LD with expanded properties.

    Returns:
        A tuple with the nodes and the parents (a dictionary: rdf_id -> parent_rdf_id).
    """
    nodes: list[Node] = []
    parents: Mapping[str, str] = {}
    for node in json_ld:
        child_node_ids = []
        node_id = node.get("@id")
        for possible_child in [
            constants.SCHEMA_ORG_DISTRIBUTION,
            constants.ML_COMMONS_RECORD_SET,
            constants.ML_COMMONS_FIELD,
            constants.ML_COMMONS_SUB_FIELD,
            constants.ML_COMMONS_SOURCE,
        ]:
            possible_child = str(possible_child)
            if possible_child in node:
                for id in node[possible_child]:
                    child_node_ids.append(id.get("@id"))
        for child_node_id in child_node_ids:
            parents[child_node_id] = node_id
    for node in json_ld:
        node_type = _get_type(node)
        if node_type is None:
            continue
        if node_type == constants.SCHEMA_ORG_DATASET:
            node_cls = Metadata
        elif node_type == constants.SCHEMA_ORG_FILE_OBJECT:
            node_cls = FileObject
        elif node_type == constants.SCHEMA_ORG_FILE_SET:
            node_cls = FileSet
        elif node_type == constants.ML_COMMONS_FIELD:
            node_cls = Field
        elif node_type == constants.ML_COMMONS_RECORD_SET:
            node_cls = RecordSet
        else:
            issues.add_error(
                f'Node should have an attribute `"@type" in "{_EXPECTED_TYPES}"`. Got'
                f' "{node_type}".'
            )
            continue

        node_id = node.get("@id")
        node_params = _parse_node_params(issues, json_ld, node)
        try:
            new_node = node_cls(issues=issues, rdf_id=node_id, **node_params)
            nodes.append(new_node)
        except TypeError:
            # TODO(marcenacp): handle the exception with dataclasses.dataclass.
            continue
    # Recreate the nodes with the whole hierarchy.
    nodes_with_parents: list[Node] = []
    for node in nodes:
        predecessors = _get_predecessors(nodes, node, parents)
        context = _get_context(predecessors)
        node_with_parents = dataclasses.replace(
            node, uid=_get_uid(predecessors), context=context
        )
        # Static analysis of the node:
        node_with_parents.check()
        nodes_with_parents.append(node_with_parents)
    return nodes_with_parents, parents


def get_entry_nodes(issues: Issues, graph: nx.MultiDiGraph) -> list[Node]:
    """Retrieves the entry nodes (without predecessors) in a graph."""
    entry_nodes = []
    for node, indegree in graph.in_degree(graph.nodes()):
        if indegree == 0:
            entry_nodes.append(node)
    # Fields should usually not be entry nodes, except if they have subFields. So we
    # check for this:
    for node in entry_nodes:
        if isinstance(node, Field) and not node.has_sub_fields:
            issues.add_error(
                f'Node "{node.uid}" is a field and has no source. Please, use'
                f" {constants.ML_COMMONS_SOURCE} to specify the source."
            )
    return entry_nodes


def _check_no_duplicate(nodes: list[Node]) -> Mapping[str, Node]:
    """Checks that no node has duplicated UID and returns the mapping `uid`->`Node`."""
    uid_to_node: Mapping[str, Node] = {}
    for node in nodes:
        if node.uid in uid_to_node:
            node.add_error(
                f"Duplicate nodes with the same identifier: {uid_to_node[node.uid]}"
            )
        uid_to_node[node.uid] = node
    return uid_to_node


def _add_node_as_entry_node(issues: Issues, graph: nx.MultiDiGraph, node: Node):
    """Add `node` as the entry node of the graph by updating `graph` in place."""
    graph.add_node(node, parent=None)
    entry_nodes = get_entry_nodes(issues, graph)
    for entry_node in entry_nodes:
        if isinstance(node, (FileObject, FileSet)):
            graph.add_edge(entry_node, node)


def _add_edge(
    issues: Issues,
    graph: nx.MultiDiGraph,
    uid_to_node: Mapping[str, Node],
    uid: str,
    node: Node,
    expected_types: type | tuple[type],
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
    issues: Issues, nodes: list[Node], parents: Mapping[str, str]
) -> nx.MultiDiGraph:
    """Converts the list of nodes to a structure graph.

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
    graph = nx.MultiDiGraph()
    uid_to_node = _check_no_duplicate(nodes)
    metadata = None
    for node in nodes:
        # Metadata
        if isinstance(node, Metadata):
            metadata = node
            continue
        parent_id = parents[node.rdf_id]
        parent = next(_node for _node in nodes if _node.rdf_id == parent_id)
        graph.add_node(node, parent=parent)
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
            for reference in references:
                # The source can be either another field...
                if (uid := _concatenate_uid(reference)) in uid_to_node:
                    # Record sets are not valid parents here.
                    # The case can arise when a Field references a record set to have a
                    # machine-readable explanation of the field (see datasets/titanic
                    # for example).
                    if not isinstance(uid_to_node[uid], RecordSet):
                        _add_edge(issues, graph, uid_to_node, uid, node, Node)
                # ...or the source can be a metadata.
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
        issues.add_error("No metadata is defined in the dataset.")
        return None, graph
    _add_node_as_entry_node(issues, graph, metadata)
    if not graph.is_directed():
        issues.add_error("Structure graph is not directed.")
    return metadata, graph
