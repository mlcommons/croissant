import dataclasses

import networkx as nx

from format.src.nodes import Node


@dataclasses.dataclass(frozen=True)
class ComputationGraph(nx.MultiDiGraph):
    graph: nx.MultiDiGraph

    @classmethod
    def from_nodes(self, nodes: list[Node]) -> "ComputationGraph":
        graph = nx.MultiDiGraph()
        for node in nodes:
            graph.add_node(node)
        return ComputationGraph(graph=graph)

    def check_graph(self):
        pass
