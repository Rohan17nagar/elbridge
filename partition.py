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

  for component in components:
    # component is a set of nodes in each component
    for pair in permutations(component, r=2):
      # if two vertices in the same component shared an edge in G, restore that edge
      if pair in G.edges():
        mst.add_edge(*pair)

  original_edge_set = set(G.edges())
  new_edge_set = set(mst.edges())
  hypotheticals = original_edge_set - new_edge_set

  return mst, hypotheticals

def main():
  G = nx.path_graph(10)
  Gp, cutset = partition(G, 3)
  nx.draw_networkx(Gp)
  plt.show()

if __name__ == '__main__':
  main()