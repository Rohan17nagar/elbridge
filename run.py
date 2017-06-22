import partition
import shape
from shapely.ops import cascaded_union

import networkx as nx
import matplotlib.pyplot as plt

import pprint

import os

def draw_graph(graph, title=""):
  pos = { n[0] : [n[1]['block'].centroid.x, n[1]['block'].centroid.y] for n in graph.nodes(data=True) }
  nx.draw_networkx(graph, pos)

  # nx.draw_networkx(graph)

  # pos = { n : n for n in graph.nodes() }
  # nx.draw_networkx(graph, pos)

  plt.title(title)
  plt.show()

def score(graph):
  comps = nx.connected_components(graph)
  num_comps = nx.number_connected_components(graph)
  goal = float(len(graph)) / num_comps

  score = 0
  for comp in comps:
    score += abs(goal - len(comp))

  return score

STEPS = 100
# starting from input partition G with a set of hypothetical edges, climb a hill
def climb(G, hypotheticals, steps=STEPS):
  cur_score = score(G)

  for t0 in range(steps):
    comps = nx.connected_components(G)
    num_comps = nx.number_connected_components(G)

    best_score = float('inf')
    best_partition_cut = [] # set of edges cut from best partition
    best_new_edge = None

    for edge in hypotheticals:
      # hypothetical edges (i,j) can either be realized towards i or towards j
      # realizing an edge towards i means adding j to V(i), where V(i) is the connected component containing i
      # valid steps are thus in a sense directional; (i,j) means "realize towards i"

      # 1. remove all edges incident to v except (these go into hyp)
      # 2. add (u,v) and remove from hyp
      # 3. for all x connected to u, remove (x, v) from hyp if it exists
      
      # first, make sure i and j aren't connected
      i, j = edge
      assert nx.has_path(G, i, j) == False

      # second, test realizing towards i, then j
      for u, v in [(i,j), (j,i)]:
        cut = G.edges(v)
        
        # create new graph
        G.remove_edges_from(cut)
        G.add_edge(u,v)

        # if this is a valid step (preserves # connected components), score it
        if nx.number_connected_components(G) == num_comps:
          new_score = score(G)
          if new_score < best_score:
            best_score = new_score
            best_partition_cut = cut
            best_new_edge = (u,v)

        # restore old graph
        G.remove_edge(u,v)
        G.add_edges_from(cut)

    if best_score >= cur_score:
      # draw_graph(G, "best overall (score {}) in {} steps".format(cur_score, t0))
      return G, cur_score

    u, v = best_new_edge
    G.add_edge(u, v)
    G.remove_edges_from(best_partition_cut)

    hypotheticals = hypotheticals.union(best_partition_cut) - {(u,v), (v,u)}
    for comp in comps:
      if u in comp:
        for x in comp:
          if (x, v) in hypotheticals:
            hypotheticals.remove((x,v))
          if (v, x) in hypotheticals:
            hypotheticals.remove((v,x))
        break

    cur_score = best_score

    # draw_graph(G, "new best graph (score {}) after {} steps".format(cur_score, t0+1))

  # draw_graph(G, "best overall (score {}) in {} steps".format(cur_score, STEPS))
  return G, cur_score

def main():
  in_dir = "data/state_shapes"
  in_file = "state_shapes"

  if os.path.exists(os.path.join(in_dir, in_file + ".pickle")):
    print("pickle found")
    G = nx.read_gpickle(os.path.join(in_dir, in_file + ".pickle"))
  else:
    G = shape.create_graph(in_dir, in_file, pickle=True, draw_shapefile=True)

  best_score = float('inf')
  best_partition = None
  for _ in range(10):
    part, hyp = partition.partition(G, 5)

    # draw_graph(part, "starting configuration with score {}".format(score(part)))
    n_part, sc = climb(part, hyp)
    # draw_graph(n_part, "ending configuration with score {}".format(sc))
    if sc < best_score:
      best_score = sc
      best_partition = n_part

  # draw_graph(best_partition, "best partition after 10 steps with score {}".format(best_score))
  regions = []
  for comp in nx.connected_components(best_partition):
    objs = [d['block'] for name in comp for _, d in filter(lambda x: x[0] == name, G.nodes(data=True))]
    regions.append(cascaded_union(objs))

  shape.plot_objects(regions, random_color=True)

def test():
  G = nx.complete_graph(10)
  part, hyp = partition.partition(G, 2)
  n_part, sc = climb(part, hyp)

if __name__ == "__main__":
  main()