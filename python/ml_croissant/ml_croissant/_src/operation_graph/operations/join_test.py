"""join_test module."""

import networkx as nx

from ml_croissant._src.operation_graph.operations import join
from ml_croissant._src.tests.nodes import empty_node


def test_str_representation():
    operation = join.Join(graph=nx.MultiDiGraph(), node=empty_node)
    assert str(operation) == "Join(node_name)"
