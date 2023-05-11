import time

import networkx as nx


def pretty_print_graph(graph: nx.Graph):
    """Pretty prints a NetworkX graph.

    Args:
        graph: Any NetworkX graph.

    Warning: this function is for debugging purposes only."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Please, install matplotlib.")
    nx.draw(graph, with_labels=True)
    temporary_file = f"/tmp/graph_{time.time()}.svg"
    plt.savefig(temporary_file)
    print(f"Generated a graph and saved it in: {temporary_file}")

def print_graph_traversal(graph: nx.Graph):
    """Pretty prints a NetworkX graph.

    Args:
        graph: Any NetworkX graph.

    Warning: this function is for debugging purposes only."""
    print(list(nx.edge_bfs(graph, orientation='original')))
