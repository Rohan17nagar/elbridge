# pylint: disable=C0103, C0200
"""Local search."""

import random
from multiprocessing import Pool
import sys

import networkx as nx
import matplotlib.pyplot as plt
from tqdm import tqdm

import shape
import utils

class State():
    """Encapsulates a state."""
    objectives = []
    master_graph = []

    def __init__(self, graph, hypotheticals, scores, chromosome):
        if not State.objectives:
            raise Exception("Class State not initalized!")
        self.graph = graph
        self.hypotheticals = hypotheticals
        self.scores = scores
        self.chromosome = chromosome

    def __hash__(self):
        return frozenset(self.hypotheticals).__hash__()

    def __eq__(self, other):
        return self.hypotheticals == other.hypotheticals

    def __repr__(self):
        return str(self.hypotheticals) + " (" + str(self.scores) + ")"

    def dominated_by(self, other_scores):
        """Returns true if some scores dominate our score."""
        as_good = True
        better = False
        for idx in range(len(self.scores)):
            if self.scores[idx] > other_scores[idx]:
                as_good = False
                break
            elif self.scores[idx] < other_scores[idx]:
                better = True

        return as_good and better

    def _gradient(self, other_scores):
        """Calculate the gradient between self and other scores."""
        out = 0
        for idx in range(len(self.scores)):
            out += (other_scores[idx] - self.scores[idx])

        return out

    @profile
    def _make_step(self, edge, undo=True):
        # pylint: disable=too-many-locals
        # if undo is False, destructively evaluate
        out = None
        i, j = edge
        adds = set() # everything added to hypotheticals
        removes = set() # everything removed from hypotheticals

        comp = lambda v: utils.get_component(self.chromosome, self.graph, v)

        i_cmp = comp(i)
        j_cmp = comp(j)
        assert i_cmp != j_cmp

        old_value = j_cmp
        self.chromosome[utils.get_index(self.graph, j)] = i_cmp

        for n in State.master_graph[j]:
            if comp(n) == i_cmp:
                if (j, n) in self.hypotheticals:
                    self.graph.add_edge(j, n)
                    self.hypotheticals.remove((j, n))
                    removes.add((j, n))
                elif (n, j) in self.hypotheticals:
                    self.graph.add_edge(n, j)
                    self.hypotheticals.remove((n, j))
                    removes.add((n, j))
                else:
                    assert False
            elif comp(n) == old_value:
                self.graph.remove_edge(j, n)
                self.hypotheticals.add((j, n))
                adds.add((j, n))

        components = utils.chromosome_to_components(self.graph, self.chromosome)
        components = list(components.values())
        cand_scores = [objective(components, self.graph) for objective
                       in State.objectives]

        if self.dominated_by(cand_scores):
            out = ((i, j), self._gradient(cand_scores))

        if undo:
            self.hypotheticals = self.hypotheticals.union(removes).difference(adds)
            self.graph.add_edges_from(adds)
            self.graph.remove_edges_from(removes)
            self.chromosome[utils.get_index(self.graph, j)] = old_value
        else:
            self.scores = cand_scores

        if out:
            return out

        return (None, 0)

    @profile
    def move_to_best_neighbor(self, sample_size):
        """Find the best neighbors of this state."""
        moves = self.hypotheticals.union([(j, i) for (i, j) in
                                          self.hypotheticals])
        samples = random.sample(moves, min(len(moves), sample_size))
        new_moves = []
        # with Pool() as p:
            # # for move in p.imap_unordered(self._make_step, samples):
            # for move in tqdm(p.imap_unordered(self._make_step, samples),
                             # total=len(samples), desc="Evaluating steps"):
                # new_moves.append(move)
        for move in samples:
            new_moves.append(self._make_step(move))
        # new_moves = list(map(self._make_step, samples))
        best_move, _, = max(new_moves, key=lambda obj: obj[1])
        if best_move is not None:
            self._make_step(best_move, undo=False)
        return best_move

    def plot(self):
        """Plot this state."""
        title = "Chromosome (" \
                + "; ".join(["{name}: {value}".format(name=str(State.objectives[idx]), value=score)
                             for idx, score in enumerate(self.scores)]) + ")"
        shapes = []
        count = 0

        for i, component in enumerate(nx.connected_component_subgraphs(self.graph)):
            color = (random.random(), random.random(), random.random())
            shapes += [(data.get('shape'), color) for _, data in component.nodes(data=True)]

            print("Component", i)
            print("Total population:",
                  sum([data.get('pop') for _, data in component.nodes(data=True)]))
            print()
            count += 1

        print("Goal size:", sum([data.get('pop')
                                 for _, data in self.graph.nodes(data=True)]) / count)

        shape.plot_shapes(shapes, title=title)

def to_input(candidates):
    """Take a set of candidates and find dependencies. Used in topological
    sorting."""
    # candidate x is dominated by candidates output[x]
    output = {i : set() for i in range(len(candidates))}
    for i, (cand, _) in enumerate(candidates):
        for j, (o_cand, _)  in enumerate(candidates):
            if cand.dominates(o_cand.scores):
                output[j].add(i)
    return output

def draw_and_highlight(graph, *nodes, pos={}, labels={}):
    """Highlight a node."""
    index = lambda node: list(graph.nodes()).index(node)
    colors = ['r'] * len(graph)
    for i in nodes:
        colors[index(i)] = 'b'
    nx.draw_networkx(graph,
                     pos=pos,
                     labels=labels,
                     node_color=colors)
    plt.show()

@profile
def optimize(candidate, pos, steps=1000, sample_size=100):
    # pylint: disable=global-statement
    """Take a solution and return a nearby local maximum."""

    graph = candidate.reconstruct_graph()
    assert State.objectives
    assert State.master_graph

    state = State(graph, candidate.hypotheticals, candidate.scores,
                  candidate.chromosome)

    # for _ in range(steps):
    for _ in tqdm(range(steps), "Taking steps", position=pos):
        new_move = state.move_to_best_neighbor(sample_size)
        if new_move is None:
            assert [state.scores[idx] >= candidate.scores[idx] for idx in
                    range(len(state.scores))]
            return state

    return state
