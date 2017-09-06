"""Partitions a graph into k connected components."""

import networkx as nx

from utils import random_subset

def partition(G, k):
    """Partition a graph into k connected components."""
    mst = nx.minimum_spanning_tree(G)
    cut = random_subset(mst.edges(), k-1)
    mst.remove_edges_from(cut)

    components = nx.connected_components(mst)
    num_comps = nx.number_connected_components(mst)
    assert num_comps == k

    part = nx.Graph()

    for component in components:
        subgraph = G.subgraph(component)
        part.add_nodes_from(subgraph.nodes(data=True))
        part.add_edges_from(subgraph.edges(data=True))

    hypotheticals = [(u, v, data) for (u, v, data) in G.edges(data=True)
                     if not part.has_edge(u, v)]

    return partition, hypotheticals, k

def test():
    """Tests partition() by cutting a cycle graph into 3 components."""
    G = nx.cycle_graph(10)
    Gp, cutset, k = partition(G, 3)

    expected_cutset = [(i, (i+1) % 10, {}) for i in range(10) if not Gp.has_edge(i, (i+1) % 10)]
    assert cutset == expected_cutset, "Found {} but expected {}".format(cutset, expected_cutset)
    assert k == 3
    
if __name__ == '__main__':
    test()
    