import partition
import shape
import scorer
from shapely.ops import cascaded_union

import networkx as nx
import matplotlib.pyplot as plt

import pprint

import os
import logging
import argparse

from tqdm import tqdm

# A step from S to N is valid iff, for all score functions f, f(N) >= f(S),
# and for at least one function f*, f*(N) > f*(S). Or, f(N) - f(S) >= 0 for all
# f and sum_f f(N) - f(S) > 0.
def differential(cur_scores, new_scores):
  diffs = [new_scores[i] - cur_scores[i] for i in range(len(cur_scores))]

  total = 0

  for diff in diffs:
    if diff < 0:
      return -1
    total += diff

  if total == 0:
    return -1

  return total

def draw_graph(graph, title=""):
  pos = { n[0] : [n[1]['block'].centroid.x, n[1]['block'].centroid.y] for n in graph.nodes(data=True) }
  nx.draw_networkx(graph, pos)

  # nx.draw_networkx(graph)

  # pos = { n : n for n in graph.nodes() }
  # nx.draw_networkx(graph, pos)

  plt.title(title)
  plt.show()

# starting from input partition G with a set of hypothetical edges, climb a hill
def climb(G, hypotheticals, steps=100, draw=False):
  cur_scores = scorer.score(G)
  orig_scores = cur_scores
  logging.info('starting scores: %d', cur_scores)

  for t0 in tqdm(range(steps), desc="Taking steps"):
    comps = nx.connected_components(G)
    num_comps = nx.number_connected_components(G)

    max_gradient = float('-inf')
    best_partition_cut = [] # set of edges cut from best partition
    best_new_edge = None

    for idx in tqdm(range(len(hypotheticals)), desc="Scanning hypotheticals", leave=True):
      edge = hypotheticals[idx]
      logging.debug('inspecting edge %s', edge)
      # hypothetical edges (i,j) can either be realized towards i or towards j
      # realizing an edge towards i means adding j to V(i), where V(i) is the connected component containing i

      # 1. remove all edges incident to v except (these go into hyp)
      # 2. add (u,v) and remove from hyp
      # 3. for all x connected to u, remove (x, v) from hyp if it exists

      # test realizing towards i, then j
      i, j, data = edge
      for u, v in [(i,j), (j,i)]:
        cut = G.edges(v, data=True)
        
        # create new graph
        G.remove_edges_from(cut)
        G.add_edge(u,v,data)

        # if this is a valid step (preserves # connected components), score it
        if nx.number_connected_components(G) == num_comps:
          new_scores = scorer.score(G)
          logging.debug('realizing %s towards %s is valid and has score %s', v, u, new_scores)

          diff = differential(cur_scores, new_scores)
          if diff is not None and diff > max_gradient:
            best_scores = new_scores
            best_partition_cut = cut
            best_new_edge = (u,v,data)

        # restore old graph
        G.remove_edge(u,v)
        G.add_edges_from(cut)

    # no neighboring step is better than the current position, so this state is Pareto-optimal
    if not any(valid_step):
      logging.info('finished in %s steps with an overall score of %s', t0, cur_scores)
      if draw:
        draw_graph(G, "best overall (score {}) in {} steps".format(cur_scores, t0))

      return G, cur_scores

    u, v, data = best_new_edge
    G.add_edge(u,v,data)
    G.remove_edges_from(best_partition_cut)

    for edge in best_partition_cut:
      if edge not in hypotheticals:
        hypotheticals.append(edge)

    # remove (u,v)/(v,u) from hypothetical edges
    orig = hypotheticals
    hypotheticals = list(filter(lambda e: not ((e[0] == u and e[1] == v) or (e[0] == v and e[1] == u)), hypotheticals))

    for comp in comps:
      if u in comp:
        # remove all hypothetical edges from anything connected to u to v
        for x in comp:
          hypotheticals = list(filter(lambda e: not ((e[0] == v and e[1] == x) or (e[0] == x and e[1] == v)),
            hypotheticals))
        break
    logging.info('updated hypothetical edge set')

    cur_scores = best_scores

    if draw:
      draw_graph(G, "new best graph (score {}) after {} steps".format(cur_scores, t0+1))


  if draw:
    draw_graph(G, "best overall (score {}) in {} steps".format(cur_scores, STEPS))
  return G, cur_scores

def main(log_level=30, runs=10, steps=100,
  data_prefix='data', shape_name='state_shapes', force_reload_graph=False):
  logging.basicConfig(level=log_level,
    format="[%(levelname)s %(asctime)s] %(filename)s@%(funcname)s [line %(lineno)d]: %(message)s")

  in_dir = os.path.join(data_prefix, shape_name)

  if not force_reload_graph and os.path.exists(os.path.join(in_dir, shape_name + ".pickle")):
    logging.info("Pickle found at %s", os.path.join(in_dir, shape_name + ".pickle"))
    G = nx.read_gpickle(os.path.join(in_dir, shape_name + ".pickle"))
    logging.info("Finished reading pickle")
  else:
    logging.info("No pickle found, reading from file")
    G = shape.create_graph(in_dir, shape_name, pickle=True)

  # best_score = float('-inf')
  # best_partition = None
  partitions = []
  scores = []
  for t0 in tqdm(range(runs), desc="Hill-climbing", leave=True):
    part, hyp = partition.partition(G, 5)

    # draw_graph(part, "starting configuration with score {}".format(scorer.score(part)))
    n_part, sc = climb(part, hyp, steps=steps)
    partitions.append(n_part)
    scores.append(sc)
    # draw_graph(n_part, "ending configuration with score {}".format(sc))

    # logging.debug("current best score: %d; new score: %d", best_score, sc)
    # if sc > best_score:
    #   best_score = sc
    #   best_partition = n_part

  plt.plot([sc[0] for sc in scores], [sc[1] for sc in scores], 'ro')
  plt.axis([min([sc[0] for sc in scores]), max([sc[0] for sc in scores]),
    min([sc[1] for sc in scores]), max([sc[1] for sc in scores])])
  plt.show()
  # draw_graph(best_partition, "best partition after 10 steps with score {}".format(best_score))
  # regions = []
  # for comp in nx.connected_components(best_partition):
  #   objs = [d['block'] for name in comp for _, d in filter(lambda x: x[0] == name, G.nodes(data=True))]
  #   regions.append(cascaded_union(objs))

  # shape.plot_objects(regions, random_color=True)

def test():
  G = nx.complete_graph(10)
  part, hyp = partition.partition(G, 2)
  n_part, sc = climb(part, hyp)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Generate an optimal gerrymander.")
  parser.add_argument('--log', help='Default logging level.',
    default='WARN', choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'])
  parser.add_argument('--runs', help='Number of starting positions from which to run hill-climbing.',
    default=10, type=int)
  parser.add_argument('--dir', help='Name of shapefiles.', default='state_shapes')
  parser.add_argument('--data', help='Data directory.', default='data')
  parser.add_argument('--steps', help='Steps per run.', default=100, type=int)
  parser.add_argument('--reload', help='Overwrite pickle.', action="store_true")

  args = parser.parse_args()

  loglevel = args.log
  log_level = getattr(logging, loglevel.upper(), None)

  runs = args.runs
  steps = args.steps

  shape_dir = args.dir
  data_dir = args.data

  reload_graph = args.reload

  main(runs=runs, steps=steps, log_level=log_level, data_prefix=data_dir, shape_name=shape_dir,
    force_reload_graph=reload_graph)