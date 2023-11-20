"""Utils for graphs."""

import time

import networkx as nx


def pretty_print_graph(graph: nx.Graph, simplify=False):
    """Pretty prints a NetworkX graph.

    Warning: this function is for debugging purposes only.

    Args:
        graph: Any NetworkX graph.
        simplify: Whether to print a simplified version of nodes.
    """
    if simplify:
        simple_graph = nx.Graph()
        for x, y in graph.edges():
            x = getattr(x, "uid", x)
            y = getattr(y, "uid", y)
            simple_graph.add_edge(x, y)
        graph = simple_graph
    agraph = nx.nx_agraph.to_agraph(graph)
    agraph.layout(prog="dot")
    temporary_file = f"/tmp/graph_{time.time()}.svg"
    agraph.draw(temporary_file, args="-Gnodesep=0.01 -Gfont_size=1", prog="dot")
    print(f"Generated a graph and saved it in: {temporary_file}")


def print_graph_traversal(graph: nx.Graph):
    """Pretty prints a NetworkX graph.

    Warning: this function is for debugging purposes only.

    Args:
        graph: Any NetworkX graph.
    """
    visited = {}
    print("--- Graph traversal ---")
    for start, end, _ in nx.edge_bfs(graph):
        for node in [start, end]:
            if node.name not in visited:
                print(f"Visited: {node.name}")
                visited[node.name] = True
    print("Done traversing the graph.")
