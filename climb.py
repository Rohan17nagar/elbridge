"""
Encapsulates a state, which consists of a partition and the set of hypothetical edges in that partition.
"""

class State():
  def __init__(self, graph, hypotheticals):
    self.G = partition
    self.hypotheticals = hypotheticals
    self.num_components = nx.num_connected_components(partition)

  def neighbors(self):
    # return a generator over the set of hypotheticals
    for (i, j, data) in self.hypotheticals:
      Gp = self.G.copy()
      Gp_hyps = self.hypotheticals.copy()

      for u, v in [(i,j), (j,i)]:
        v_neighbors = self.G.edges(v, data=True)
        u_component = nx.node_connected_component(G, u)

        Gp.remove_edges_from(v_neighbors)
        Gp.add_edge(u, v, data)

        if nx.num_connected_components(self.G) == self.num_components:
          # (i,j) is no longer hypothetical
          Gp_hyps.remove((i,j,data))

          # all removed edges from v to its old neighbors are now hypothetical
          for v_edge in v_neighbors:
            assert v_edge not in Gp_hyps
            Gp_hyps.add(v_edge)

          # all edges from nodes in u's component to v are now realized
          for node in u_component:
            for (x, y, data) in Gp_hyps:
              if (x == node and y == v) or (x == v and y == node):
                Gp_hyps.remove(x, y, data)
                Gp.add_edge(x, y, data)

          yield State(Gp, Gp_hyps)


def differential(new_scores, cur_scores):
  diffs = [new_scores[i] - cur_scores[i] for i in range(len(cur_scores))]

  total = 0

  for diff in diffs:
    if diff < 0:
      return -1
    total += diff

  if total == 0:
    return -1

  return total


def draw_state(state, title=""):
  graph = state.G
  pos = { n[0] : [n[1]['block'].centroid.x, n[1]['block'].centroid.y] for n in graph.nodes(data=True) }
  nx.draw_networkx(graph, pos)

  # nx.draw_networkx(graph)

  # pos = { n : n for n in graph.nodes() }
  # nx.draw_networkx(graph, pos)

  plt.title(title)
  plt.show()

def build_frontier(S, steps=100, draw_steps=False, draw_final=False):
  cur_state = S
  cur_score = scorer.score(S)

  for t0 in tqdm(range(steps), desc="Taking steps"):
    best_neighbor = None
    best_score = None
    best_diff = -1

    for N in tqdm(cur_state.neighbors(), desc="Evaluating neighbors", leave=True):
      n_score = scorer.score(N)
      n_diff = differential(n_score, cur_score)

      if n_diff > best_diff:
        best_neighbor = N
        best_score = n_score
        best_diff = n_diff

    if best_neighbor is None:
      # no neighbor of cur_state is better than cur_state

      if draw_final:
        draw_state(cur_state, title="Final graph (score {score} after {steps} steps"
          .format(score=cur_score, steps=t0 + 1))

      return cur_state, cur_score

    cur_score = best_score
    cur_state = best_neighbor

    if draw_steps:
      draw_state(cur_state, title="New graph (score {score} after {steps} steps"
        .format(score=cur_state, steps=t0 + 1))

  if draw_final:
    draw_state(cur_state, title="Final graph (score {score} after {steps} steps"
      .format(score=cur_score, steps=steps))

  return cur_state, cur_score
