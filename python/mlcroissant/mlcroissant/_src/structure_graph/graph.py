"""Structure graph module.

The goal of this module is the static analysis of the JSON file. We convert the initial
JSON to a so-called "structure graph", which is a Python representation of the JSON
containing the nodes (Metadata, FileObject, etc) and the hierarchy between them. In the
process of parsing all the nodes, we also check that no information is missing and raise
issues (errors or warnings) when necessary. See the docstring of
`from_nodes_to_structure_graph` for more information.

The important functions of this module are:
- from_file_to_jsonld           file -> JSON-LD
- from_nodes_to_graph           Metadata -> graph

TODO(https://github.com/mlcommons/croissant/issues/114):
A lot of methods in this file share common data structures (issues, graph, folder, etc),
so they should be grouped under a common `StructureGraph` class.
"""

from __future__ import annotations

import json

from etils import epath
import networkx as nx

from mlcroissant._src.core import constants
from mlcroissant._src.core.types import Json
from mlcroissant._src.structure_graph.base_node import Node
from mlcroissant._src.structure_graph.nodes.file_object import FileObject
from mlcroissant._src.structure_graph.nodes.file_set import FileSet
from mlcroissant._src.structure_graph.nodes.record_set import RecordSet


def from_file_to_json(filepath: epath.PathLike) -> tuple[epath.Path, Json]:
    """Loads the file as a JSON-LD.

    Args:
        filepath: The path to the file as a str or a path. The path can be absolute or
            relative.

    Returns:
        A tuple with the absolute path to the folder and the JSON-LD.
    """
    filepath = epath.Path(filepath).expanduser().resolve()
    if not filepath.exists():
        raise ValueError(f"File {filepath} does not exist.")
    with filepath.open() as f:
        data = json.load(f)
    return filepath.parent, data


def from_nodes_to_graph(metadata) -> nx.MultiDiGraph:
    """Converts the metadata to a structure graph linking nodes to their sources."""
    graph = nx.MultiDiGraph()
    # Bind graph to nodes:
    for node in metadata.nodes():
        graph.add_node(node)
    uuid_to_node = _check_no_duplicate(metadata)
    for node in metadata.distribution:
        if node.contained_in:
            for uuid in node.contained_in:
                _add_edge(graph, uuid_to_node, uuid, node)
    for record_set in metadata.record_sets:
        for field in record_set.fields:
            _add_edge(graph, uuid_to_node, record_set.uuid, field)
            for origin in [field.source, field.references]:
                if origin:
                    _add_edge(graph, uuid_to_node, origin.uuid, record_set)
            for sub_field in field.sub_fields:
                for origin in [sub_field.source, sub_field.references]:
                    if origin:
                        _add_edge(graph, uuid_to_node, origin.uuid, record_set)
    # `Metadata` are used as the entry node.
    _add_node_as_entry_node(graph, metadata)
    return graph


def _get_entry_nodes(graph: nx.MultiDiGraph, node: Node) -> list[Node]:
    """Retrieves the entry nodes (without predecessors) in a graph."""
    ctx = node.ctx
    entry_nodes: list[Node] = []
    for node, indegree in graph.in_degree(graph.nodes()):
        if indegree == 0:
            entry_nodes.append(node)  # pytype: disable=container-type-mismatch
    # Fields should usually not be entry nodes, except if they have subFields. So we
    # check for this:
    for node in entry_nodes:
        if isinstance(node, RecordSet) and not node.data:
            for field in node.fields:
                if not field.source:
                    field.add_error(
                        f'Node "{field.uuid}" is a field and has no source. Please, use'
                        f" {constants.ML_COMMONS_SOURCE(ctx)} to specify the source."
                    )
                else:
                    field.add_error(
                        f"Malformed source data: {field.source.uuid}. It does not refer"
                        " to any existing node. Have you used"
                        f" {constants.ML_COMMONS_FIELD(ctx)} or"
                        f" {constants.SCHEMA_ORG_DISTRIBUTION} to indicate the source"
                        " field or the source distribution? If you specified a field,"
                        " it should contain all the names from the RecordSet separated"
                        ' by `/`, e.g.: "record_set_name/field_name"'
                    )
    return entry_nodes  # pytype: disable=bad-return-type


def _check_no_duplicate(metadata) -> dict[str, Node]:
    """Checks no node has duplicated UUID and returns the mapping `uuid`->`Node`."""
    uuid_to_node: dict[str, Node] = {}
    for node in metadata.nodes():
        if node.uuid in uuid_to_node:
            node.add_error(
                "Duplicate nodes with the same identifier:"
                f" {uuid_to_node[node.uuid].uuid}"
            )
        uuid_to_node[node.uuid] = node
    return uuid_to_node


def _add_node_as_entry_node(graph: nx.MultiDiGraph, node: Node):
    """Add `node` as the entry node of the graph by updating `graph` in place."""
    graph.add_node(node, parent=None)
    entry_nodes = _get_entry_nodes(graph, node)
    for entry_node in entry_nodes:
        if isinstance(node, (FileObject, FileSet)):
            graph.add_edge(entry_node, node)


def _add_edge(
    graph: nx.MultiDiGraph,
    uuid_to_node: dict[str, Node],
    uuid: str,
    node: Node,
):
    """Adds an edge in the structure graph."""
    if uuid not in uuid_to_node:
        node.add_error(
            f'There is a reference to node with UUID "{uuid}" in node "{node.uuid}",'
            " but this node doesn't exist."
        )
        return
    graph.add_edge(uuid_to_node[uuid], node)
