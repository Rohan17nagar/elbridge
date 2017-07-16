import statistics
import networkx as nx
import logging
from shapely.ops import cascaded_union
from math import pi
import time

# implement some score functions on graphs
# input to a score function: networkx.Graph
# output: score
# goal should *always* be to maximize

# takes a graph G = (V,E)
# let N = |V|, V1...Vd be the connected components
# returns sum_i abs(|Vi| - N/d)
def size_deviation(graph):
  comps = nx.connected_components(graph)
  num_comps = nx.number_connected_components(graph)
  goal = float(len(graph)) / num_comps

  score = 0
  for comp in comps:
    score += abs(goal - len(comp))

  return -1 * score

# returns the Polsby-Popper score of a shapefile, area / area of circle with same perimeter
def polsby_popper(graph):
  comps = nx.connected_components(graph)
  num_comps = nx.number_connected_components(graph)

  average = 0

  for comp in comps:
    subgraph = graph.subgraph(comp)
    area = sum([graph.node[n]['block'].area for n in comp])
    length = sum([graph.node[n]['block'].length for n in comp])
    for (u,v,data) in subgraph.edges(data=True):
      length -= 2 * data['border']
    average += 4 * pi * area / (length ** 2)

  return average / num_comps

def score(state):
  graph = state.G
  return [size_deviation(graph), polsby_popper(graph)]