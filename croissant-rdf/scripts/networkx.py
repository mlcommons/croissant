import rdflib
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

__author__ = "James Wilsenach"

# Load RDF Graph
g = rdflib.Graph()
g.parse("huggingface_10.ttl", format="turtle")  # Replace with your Turtle file

# Map predicates to unique integer values
predicate_map = {p: i for i, p in enumerate(set(g.predicates()))}


inverse_predicate_map = {v: k for k, v in predicate_map.items()}
creatorid = [predicate_map[k] for k in predicate_map if k if 'creator' in str(k)][0]
nameid = [predicate_map[k] for k in predicate_map if k if 'name' in str(k)][0]
keywordid = [predicate_map[k] for k in predicate_map if k if 'keyword' in str(k)][0]
print(creatorid)


# Create a directed graph
G = nx.DiGraph()
creators = {}

creatornames = {}
# Add edges with integer labels
for subj, pred, obj in g:
    if predicate_map[pred] == nameid:
        creatornames[subj] = obj

# Add edges with integer labels
for subj, pred, obj in g:
    if predicate_map[pred] in [creatorid]:
        # print(predicate_map[pred])
        G.add_edge(str(creatornames[subj]), str(creatornames[obj]), label='creat')
        # print(pred)
    elif predicate_map[pred] in [keywordid]:
        G.add_edge(str(creatornames[subj]), str(obj), label='key')


# Convert to an undirected simple graph (ignoring multiple edges and directions)
G_simple = nx.Graph(G)

# Check if the simple graph is connected
is_connected =  nx.is_connected(G_simple)
print("The induced simple graph is connected. Proceeding with visualization.")

# Layout for visualization
pos = nx.spring_layout(G)  

plt.figure(figsize=(12, 8))

# Draw nodes
nx.draw(G, pos, with_labels=True, node_color='skyblue', node_size=1000, 
        font_size=10, font_color='black', edge_color='gray', width=1, alpha=0.8)

# Draw edge labels (relationship type integers)
edge_labels = {(u, v): d['label'] for u, v, d in G.edges(data=True)}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=10)

plt.title("RDF Graph Adjacency Matrix Visualization")
plt.show()

# Convert to adjacency matrix
nodes = list(G.nodes())
adj_matrix = np.zeros((len(nodes), len(nodes)), dtype=int)

for i, src in enumerate(nodes):
    for j, dst in enumerate(nodes):
        if G.has_edge(src, dst):
            adj_matrix[i, j] = G[src][dst]['label']

# print("\nAdjacency Matrix:\n", adj_matrix)
