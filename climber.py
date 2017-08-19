import partition
import scorer
from utils import random_subset

import networkx as nx
import matplotlib.pyplot as plt
from tqdm import tqdm

from pathos.multiprocessing import ThreadingPool as TPool, ProcessingPool as PPool
import time

import threading

"""
Encapsulates a state, which consists of a partition and the set of hypothetical edges in that partition.
"""
class State():
  def __init__(self, graph, hypotheticals, k, score=None):
    self.G = graph
    self.hypotheticals = hypotheticals
    self.k = k
    self.score = score if score is not None else scorer.score(self)

  def evaluate_neighbor(self, args):
    u, v, data = args
    v_neighbors = self.G.edges(v, data=True)

    self.G.remove_edges_from(v_neighbors)
    self.G.add_edge(u, v, data)

    if nx.number_connected_components(self.G) == self.k:
      n_score = scorer.score(self)
      n_gradient = differential(n_score, self.score)

      self.G.remove_edge(u, v)
      self.G.add_edges_from(v_neighbors)

      return u, v, data, v_neighbors, n_score, n_gradient
    else:
      return u, v, data, v_neighbors, -1, -1

  def best_neighbor(self):
    best_score = None
    best_cut = None
    best_edge = None
    best_gradient = 0

    pool = PPool()
    grads = []

    # for x in tqdm(pool.map(self.evaluate_neighbor, self.hypotheticals)):
    #   grads.append(x)

    # for x in tqdm(pool.map(self.evaluate_neighbor, [(j, i, d) for (i, j, d) in self.hypotheticals])):
    #   grads.append(x)

    grads += pool.map(self.evaluate_neighbor, self.hypotheticals)
    grads += pool.map(self.evaluate_neighbor, [(j, i, d) for (i, j, d) in self.hypotheticals])

    best_grad = max(grads, key=lambda x: x[5])

    i, j, data, best_cut, best_score, grad = best_grad
    best_edge = (i, j, data)

    if grad <= 0: # no valid (connected or better) neighbor
      return None

    Gp = self.G.copy()
    Gp_hyps = self.hypotheticals.copy()

    # (i,j) is no longer hypothetical
    Gp.add_edge(i, j, data)

    try:
      Gp_hyps.remove((i, j, data))
    except ValueError:
      Gp_hyps.remove((j, i, data))

    # all removed edges from v to its old neighbors are now hypothetical
    for v_edge in best_cut:
      assert v_edge not in Gp_hyps
      Gp.remove_edge(v_edge[0], v_edge[1])
      Gp_hyps.append(v_edge)

    # all edges from nodes in u's component to v are now realized
    u_component = nx.node_connected_component(self.G, i)
    for node in u_component:
      for (x, y, data) in Gp_hyps:
        if (x == node and y == j) or (x == j and y == node):
          Gp_hyps.remove((x, y, data))
          Gp.add_edge(x, y, data)

    return State(Gp, Gp_hyps, self.k, best_score)

def differential(new_scores, cur_scores):
  diffs = [scorer.WEIGHTS[i] * new_scores[i] - scorer.WEIGHTS[i] * cur_scores[i]
              for i in range(len(cur_scores))]
  total = 0

  for diff in diffs:
    # if diff < 0:
    #   return -1
    total += diff

  return total

  # return sum(diffs)


def draw_state(state, title=""):
  graph = state.G
  pos = { n[0] : [n[1]['block'].centroid.x, n[1]['block'].centroid.y]
    for n in graph.nodes(data=True) }
  nx.draw_networkx(graph, pos)

  # nx.draw_networkx(graph)

  # pos = { n : n for n in graph.nodes() }
  # nx.draw_networkx(graph, pos)

  plt.title(title)
  plt.show()

# Starting at a state S, follow the path of steepest ascent until no better neighbors exist.
def find_maximum(S, steps=100, draw_steps=False, draw_final=False):
  cur_state = S

  for t0 in range(steps):
  #for t0 in tqdm(range(steps), desc="Taking steps"):
    best_neighbor = cur_state.best_neighbor()

    if best_neighbor is None:
      # no neighbor of cur_state is better than cur_state
      if draw_final:
        draw_state(cur_state, title="Final graph (score {score} after {steps} steps"
          .format(score=cur_state.score, steps=t0 + 1))

      return cur_state

    cur_state = best_neighbor

    if draw_steps:
      draw_state(cur_state, title="New graph (score {score} after {steps} steps"
        .format(score=cur_state.score, steps=t0 + 1))

    print(threading.get_ident(), t0, cur_state.score)

  if draw_final:
    draw_state(cur_state, title="Final graph (score {score} after {steps} steps"
      .format(score=cur_state.score, steps=steps))

  return cur_state

def call_find_max(data):
  G, k = data
  starter = partition.partition(G, k)
  start = State(*starter)
  return find_maximum(start)

# Given a graph G, approximate the Pareto frontier with {samples} starting points.
def find_frontier(G, k, samples=100):
  pool = TPool() # pool for partition generation
  # frontier = []
  # for x in tqdm(pool.map(call_find_max, [(G, k)] * samples), desc="Starting..."):
  #   frontier.append(x)

  frontier = pool.map(call_find_max, [(G, k)] * samples)

  filtered_frontier = []
  for A in frontier:
    found = False
    for B in frontier:
      diff = differential(B.score, A.score)
      if diff > 0:
        found = True
        break

    if not found:
      filtered_frontier.append(A)

  best_scores = [state.score for state in frontier if state in filtered_frontier]
  other_scores = [state.score for state in frontier if state not in filtered_frontier]

  print("frontier:", best_scores)
  print("others:", other_scores)

  plt.hold(True)
  fig = plt.figure()
  ax = fig.add_subplot(111)
  plt.scatter(*zip(*best_scores), c='red')
  plt.scatter(*zip(*other_scores), c='grey')

  # for score in best_scores:
  #   ax.annotate('({:.2f}, {:.2f})'.format(*score), xy=score, textcoords='data')

  # plt.grid()
  plt.show()

  # BELOW CODE: draws best partition when one exists; assumes shapefile graph
  # draw_graph(best_partition, "best partition after 10 steps with score {}".format(best_score))
  # regions = []
  # for comp in nx.connected_components(best_partition):
  #   objs = [d['block'] for name in comp for _, d in filter(lambda x: x[0] == name, G.nodes(data=True))]
  #   regions.append(cascaded_union(objs))

  # shape.plot_objects(regions, random_color=True)
