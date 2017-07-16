import networkx as nx
from itertools import permutations
import matplotlib.pyplot as plt

# create a spanning tree
# choose k-1 random edges
# remove
# recreate subgraphs

# pick k random elements of set
import random
def random_subset(iterator, K):
  result = []
  N = 0

  for item in iterator:
    N += 1
    if len( result ) < K:
      result.append( item )
    else:
      s = int(random.random() * N)
      if s < K:
        result[ s ] = item

  return result

# partition an input graph into k connected components
# return (new graph, hypothetical edges)
def partition(G, k):
  mst = nx.minimum_spanning_tree(G)
  cut = random_subset(mst.edges(), k-1)
  mst.remove_edges_from(cut)

  components = nx.connected_components(mst)

  partition = nx.Graph()

  for component in components:
    subgraph = G.subgraph(component)
    partition.add_nodes_from(subgraph.nodes(data=True))
    partition.add_edges_from(subgraph.edges(data=True))

  hypotheticals = [(u,v,data) for (u,v,data) in G.edges(data=True)
    if not partition.has_edge(u,v) and not partition.has_edge(v,u)]

  return partition, hypotheticals

def main():
  G = nx.cycle_graph(10)
  Gp, cutset = partition(G, 3)
  # nx.draw_networkx(Gp)
  # plt.show()

if __name__ == '__main__':
  main()