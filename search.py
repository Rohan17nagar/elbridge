# pylint: disable=C0103, C0200
"""Local search."""

import random
from multiprocessing import Pool

import networkx as nx
import matplotlib.pyplot as plt
from tqdm import tqdm

import objectives
import shape
import utils

class State():
    """Encapsulates a state."""
    objectives = []

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

    @staticmethod
    def refine_candidate(candidate, block_graph):
        """Given a block graph, only keep connections between blocks in the same component.

        Returns a state."""
        county_graph = candidate.reconstruct_graph()
        county_districts = nx.connected_components(county_graph)

        # county --> index of district
        county_to_district = {}
        for i, component in enumerate(county_districts):
            for node in component:
                county_to_district[node] = i

        graph = block_graph.copy()

        hypotheticals = set()

        # remove edge (i,j) if c2d[i] != c2d[j]
        edges = list(graph.edges())
        for i, j in edges:
            county = lambda n: n[:5]
            if county_to_district[county(i)] != county_to_district[county(j)]:
                graph.remove_edge(i, j)
                hypotheticals.add((i, j))

        return State(graph, hypotheticals, candidate.scores,
                     candidate.chromosome)

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
    def _make_step(self, edge):
        out = None
        i, j = edge
        adds = set() # everything added to hypotheticals
        removes = set() # everything removed from hypotheticals

        i_idx = utils.get_index(self.graph, i)
        j_idx = utils.get_index(self.graph, j)
        assert self.chromosome[i_idx] != self.chromosome[j_idx]

        old_value = self.chromosome[j_idx]
        self.chromosome[j_idx] = self.chromosome[i_idx]

        # get the neighbors of j
        j_edges = list(self.graph.edges(j))
        for j_edge in j_edges:
            # remove them from the graph
            self.graph.remove_edge(*j_edge)

            # add them to the hypothetical set
            self.hypotheticals.add(j_edge)
            adds.add(j_edge)

        # add (i, j) to graph
        self.graph.add_edge(i, j)

        # remove (i, j) from hypotheticals
        if (i, j) in self.hypotheticals:
            self.hypotheticals.remove((i, j))
            removes.add((i, j))
        else:
            self.hypotheticals.remove((j, i))
            removes.add((j, i))

        components = utils.chromosome_to_components(self.graph, self.chromosome)
        i_component = components[self.chromosome[i_idx]]

        # add (i', j) to graph, where i' is in the cc of i and (i', j) is in hypotheticals
        for node, _ in i_component:
            if (node, j) in self.hypotheticals:
                self.graph.add_edge(node, j)
                self.hypotheticals.remove((node, j))
                removes.add((node, j))
            elif (j, node) in self.hypotheticals:
                self.graph.add_edge(j, node)
                self.hypotheticals.remove((j, node))
                removes.add((j, node))

        components = list(components.values())

        cand_scores = [objective(components, self.graph) for objective
                       in State.objectives]

        if self.dominated_by(cand_scores):
            # new_g = self.graph.copy()
            new_g = nx.Graph(self.graph)
            new_h = self.hypotheticals.copy()
            new_c = self.chromosome.copy()
            out = (State(new_g, new_h, cand_scores, new_c), (i, j),
                   self._gradient(cand_scores))

        self.hypotheticals = self.hypotheticals.union(removes).difference(adds)
        self.graph.add_edges_from(adds)
        self.graph.remove_edges_from(removes)
        self.chromosome[j_idx] = old_value

        if out:
            return out
        else:
            return (self, None, 0)

    @profile
    def best_neighbor(self, sample_size):
        """Find the best neighbors of this state."""
        moves = self.hypotheticals.union([(j, i) for (i, j) in
                                          self.hypotheticals])
        samples = random.sample(moves, min(len(moves), sample_size))

        # with Pool() as p:
        new_states = list(map(self._make_step, samples))
        best_state, best_move, _, = max(new_states, key=lambda obj: obj[2])
        return best_state, best_move

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

SEEN = {}
@profile
def optimize(candidate, steps=1000, sample_size=100):
    # pylint: disable=global-statement
    """Take a solution and return a nearby local maximum."""

    graph = candidate.reconstruct_graph()
    assert State.objectives

    state = State(graph, candidate.hypotheticals, candidate.scores,
                  candidate.chromosome)

    global SEEN
    if state in SEEN:
        return SEEN[state]

    nc = lambda state, n: utils.get_component(state.chromosome, state.graph, n)
    intermediates = []
    for _ in range(steps):
        new_state, new_move = state.best_neighbor(sample_size)
        if new_move is None:
            assert [state.scores[idx] >= candidate.scores[idx] for idx in
                    range(len(state.scores))]
            return state
        else:
            assert nc(new_state, new_move[0]) == nc(state, new_move[0])
            assert nc(new_state, new_move[1]) != nc(state, new_move[1])
            assert nc(new_state, new_move[0]) == nc(new_state, new_move[1])
            assert state.dominated_by(new_state.scores), str(state.scores) + " " \
                                                         + str(new_state.scores)

        intermediates.append(state)
        state = new_state

    for st in intermediates:
        SEEN[st] = state
    SEEN[state] = state

    return state
