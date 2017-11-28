# pylint: disable=C0103, C0200
"""Local search."""

import random

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

    @profile
    def best_neighbor(self, sample_size):
        """Find the best neighbors of this state."""
        samples = random.sample(self.hypotheticals, min(len(self.hypotheticals), sample_size))

        best_state = self
        best_move = None

        for ix, jx in samples:
            for i, j in [(ix, jx), (jx, ix)]:
                print("evaluating move", i, j)
                adds = set() # everything added to hypotheticals
                removes = set() # everything removed from hypotheticals

                print("old chromosome", self.chromosome)
                i_idx = utils.get_index(self.graph, i)
                j_idx = utils.get_index(self.graph, j)
                print("index of i and value", i_idx, self.chromosome[i_idx])
                print("index of j and value", j_idx, self.chromosome[j_idx])

                assert self.chromosome[i_idx] != self.chromosome[j_idx]

                old_value = self.chromosome[j_idx]
                self.chromosome[j_idx] = self.chromosome[i_idx]
                print("index of i and value", i_idx, self.chromosome[i_idx])
                print("index of j and value", j_idx, self.chromosome[j_idx])
                print("new chromosome", self.chromosome)

                # get the neighbors of j
                j_edges = list(self.graph.edges(j))
                for edge in j_edges:
                    # remove them from the graph
                    self.graph.remove_edge(*edge)

                    # add them to the hypothetical set
                    self.hypotheticals.add(edge)
                    adds.add(edge)

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

                if best_state.dominated_by(cand_scores):
                    best_g = self.graph.copy()
                    best_h = self.hypotheticals.copy()
                    best_c = self.chromosome.copy()
                    best_state = State(best_g, best_h, cand_scores, best_c)
                    best_move = (i, j)

                self.hypotheticals = self.hypotheticals.union(removes).difference(adds)
                self.graph.add_edges_from(adds)
                self.graph.remove_edges_from(removes)
                self.chromosome[j_idx] = old_value

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
def optimize(candidate, steps=1000, sample_size=1000):
    # pylint: disable=global-statement
    """Take a solution and return a nearby local maximum."""

    graph = candidate.reconstruct_graph()
    print("ccomps at start", list(nx.connected_components(graph)))
    print("score at start", candidate.scores)

    State.objectives = [objectives.PopulationEquality(graph)]

    state = State(graph, candidate.hypotheticals, candidate.scores,
                  candidate.chromosome)

    nc = lambda state, n: utils.get_component(state.chromosome, state.graph, n)
    # nx.draw_networkx(state.graph,
                     # pos={n: n for n in graph},
                     # labels={n: str(n) + " (" + str(nc(state, n)) + ")" for n in
                             # graph})
    # plt.show()


    for _ in range(steps):
        global SEEN
        if state in SEEN:
            state = SEEN[state]
            continue

        new_state, new_move = state.best_neighbor(sample_size)
        print("making move", new_move, "with score", new_state.scores)
        print(list(nx.connected_components(new_state.graph)))
        print(new_state.chromosome)
        if new_move is None:
            assert [state.scores[idx] >= candidate.scores[idx] for idx in
                    range(len(state.scores))]
            # nx.draw_networkx(state.graph,
                             # pos={n: n for n in graph},
                             # labels={n: str(n) + " (" + str(nc(state, n)) + ")" for n in
                                     # graph})
            # plt.show()
            return state
        else:
            assert nc(new_state, new_move[0]) == nc(state, new_move[0])
            assert nc(new_state, new_move[1]) != nc(state, new_move[1])
            assert nc(new_state, new_move[0]) == nc(new_state, new_move[1])
            print("first comp", nc(new_state, new_move[0]))
            print("second comp", nc(new_state, new_move[1]))
            # draw_and_highlight(state.graph, *new_move,
                               # pos={n: n for n in new_state.graph.nodes()},
                               # labels={n: str(n) + " (" + str(nc(state, n)) + ")" for n
                                       # in state.graph.nodes()})
            # draw_and_highlight(new_state.graph, *new_move,
                               # pos={n: n for n in new_state.graph.nodes()},
                               # labels={n: str(n) + " (" + str(nc(new_state, n)) + ")" for n
                                       # in state.graph.nodes()})
            assert state.dominated_by(new_state.scores), str(state.scores) + " " \
                                                         + str(new_state.scores)
        SEEN[state] = new_state
        state = new_state

    # nx.draw_networkx(state.graph,
                     # pos={n: n for n in graph},
                     # labels={n: str(n) + " (" + str(nc(state, n)) + ")" for n in
                             # graph})
    # plt.show()
    return state
