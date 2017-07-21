import networkx as nx

from utils import random_subset

# create a spanning tree
# choose k-1 random edges
# remove
# recreate subgraphs

# partition an input graph into k connected components
# return (new graph, hypothetical edges)
def partition(G, k):
  mst = nx.minimum_spanning_tree(G)
  cut = random_subset(mst.edges(), k-1)
  mst.remove_edges_from(cut)

  components = nx.connected_components(mst)
  num_comps = nx.number_connected_components(mst)
  assert num_comps == k

  partition = nx.Graph()

  for component in components:
    subgraph = G.subgraph(component)
    partition.add_nodes_from(subgraph.nodes(data=True))
    partition.add_edges_from(subgraph.edges(data=True))

  hypotheticals = [(u,v,data) for (u,v,data) in G.edges(data=True)
    if not partition.has_edge(u,v)]

  return partition, hypotheticals

def test():
  G = nx.cycle_graph(10)
  Gp, cutset = partition(G, 3)

  expected_cutset = [(i, (i+1) % 10, {}) for i in range(10) if not Gp.has_edge(i,(i+1) % 10)]
  try:
    assert cutset == expected_cutset
  except AssertionError:
    print("found", cutset)
    print("expected", expected_cutset)

if __name__ == '__main__':
  test()