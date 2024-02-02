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
from mlcroissant._src.structure_graph.nodes.field import Field
from mlcroissant._src.structure_graph.nodes.file_object import FileObject
from mlcroissant._src.structure_graph.nodes.file_set import FileSet


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
        node.ctx.graph = graph
        graph.add_node(node)
    uid_to_node = _check_no_duplicate(metadata)
    for node in metadata.distribution:
        if node.contained_in:
            for uid in node.contained_in:
                _add_edge(graph, uid_to_node, uid, node)
    for record_set in metadata.record_sets:
        for field in record_set.fields:
            if record_set.data:
                _add_edge(graph, uid_to_node, record_set.uid, field)
            for origin in [field.source, field.references]:
                if origin:
                    _add_edge(graph, uid_to_node, origin.uid, field)
            for sub_field in field.sub_fields:
                for origin in [sub_field.source, sub_field.references]:
                    if origin:
                        _add_edge(graph, uid_to_node, origin.uid, sub_field)
    # `Metadata` are used as the entry node.
    _add_node_as_entry_node(graph, metadata)
    return graph


def _get_entry_nodes(graph: nx.MultiDiGraph, node: Node) -> list[Node]:
    """Retrieves the entry nodes (without predecessors) in a graph."""
    ctx = node.ctx
    entry_nodes: list[Node] = []
    for node, indegree in graph.in_degree(graph.nodes()):
        if indegree == 0:
            entry_nodes.append(node)
    # Fields should usually not be entry nodes, except if they have subFields. So we
    # check for this:
    for node in entry_nodes:
        if isinstance(node, Field) and not node.sub_fields and not node.data:
            if not node.source:
                node.add_error(
                    f'Node "{node.uid}" is a field and has no source. Please, use'
                    f" {constants.ML_COMMONS_SOURCE(ctx)} to specify the source."
                )
            else:
                uid = node.source.uid
                node.add_error(
                    f"Malformed source data: {uid}. It does not refer to any existing"
                    f" node. Have you used {constants.ML_COMMONS_FIELD(ctx)} or"
                    f" {constants.SCHEMA_ORG_DISTRIBUTION} to indicate the source field"
                    " or the source distribution? If you specified a field, it should"
                    " contain all the names from the RecordSet separated by `/`, e.g.:"
                    ' "record_set_name/field_name"'
                )
    return entry_nodes


def _check_no_duplicate(metadata) -> dict[str, Node]:
    """Checks that no node has duplicated UID and returns the mapping `uid`->`Node`."""
    uid_to_node: dict[str, Node] = {}
    for node in metadata.nodes():
        if node.uid in uid_to_node:
            node.add_error(
                f"Duplicate nodes with the same identifier: {uid_to_node[node.uid].uid}"
            )
        uid_to_node[node.uid] = node
    return uid_to_node


def _add_node_as_entry_node(graph: nx.MultiDiGraph, node: Node):
    """Add `node` as the entry node of the graph by updating `graph` in place."""
    graph.add_node(node, parent=None)
    entry_nodes = _get_entry_nodes(graph, node)
    for entry_node in entry_nodes:
        if isinstance(node, (FileObject, FileSet)):
            graph.add_edge(entry_node, node)


def _add_edge(
    graph: nx.MultiDiGraph,
    uid_to_node: dict[str, Node],
    uid: str,
    node: Node,
):
    """Adds an edge in the structure graph."""
    if uid not in uid_to_node:
        node.add_error(
            f'There is a reference to node named "{uid}" in node "{node.uid}", but this'
            " node doesn't exist."
        )
        return
    graph.add_edge(uid_to_node[uid], node)
