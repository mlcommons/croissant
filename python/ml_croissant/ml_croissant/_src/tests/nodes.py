"""Testing utils for `Node`."""

from ml_croissant._src.core.issues import Issues
from ml_croissant._src.structure_graph.base_node import Node
from ml_croissant._src.structure_graph.nodes import Field, FileObject, FileSet
import networkx as nx
from rdflib import term


class _EmptyNode(Node):
    def check(self):
        pass


empty_node = _EmptyNode(
    issues=Issues(),
    bnode=term.BNode("rdf_id"),
    graph=nx.MultiDiGraph(),
    name="node_name",
    parents=(),
)

empty_field = Field(
    issues=Issues(),
    bnode=term.BNode("rdf_id"),
    graph=nx.MultiDiGraph(),
    name="field_name",
    parents=(),
)

empty_file_object = FileObject(
    issues=Issues(),
    bnode=term.BNode("rdf_id"),
    graph=nx.MultiDiGraph(),
    name="file_object_name",
    parents=(),
)

empty_file_set = FileSet(
    issues=Issues(),
    bnode=term.BNode("rdf_id"),
    graph=nx.MultiDiGraph(),
    name="file_set_name",
    parents=(),
)
