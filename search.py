# pylint: disable=C0103, C0200
"""Local search."""

import random
import pprint

import networkx as nx
from toposort import toposort
import matplotlib.pyplot as plt
from tqdm import tqdm

from objectives import OBJECTIVES, DISTRICTS
import shape

class State():
    """Encapsulates a state."""

    objectives = []

    def __init__(self, graph, hypotheticals, scores):
        if not State.objectives:
            raise Exception("Class State not initalized!")
        self.graph = graph
        self.hypotheticals = hypotheticals
        self.scores = scores

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

        return State(graph, hypotheticals, candidate.scores)   

    def dominated_by(self, other_scores):
        """Returns true if some scores dominate our score."""
        as_good = True
        better = False
        for idx in range(len(self.scores)):
            if self.scores[idx] < other_scores[idx]:
                as_good = False
                break
            elif self.scores[idx] > other_scores[idx]:
                better = True

        return as_good and better

    def best_neighbors(self, sample_size):
        """Find the best neighbors of this state."""
        samples = random.sample(self.hypotheticals, min(len(self.hypotheticals), sample_size))

        neighbors = []

        for i, j in samples:
            adds = set() # everything added to hypotheticals
            removes = set() # everything removed from hypotheticals
            
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
            self.hypotheticals.remove((i, j))
            removes.add((i, j))

            # add (i', j) to graph, where i' is in the cc of i and (i', j) is in hypotheticals
            for node in nx.node_connected_component(self.graph, i):
                if (node, j) in self.hypotheticals:
                    self.graph.add_edge(node, j)
                    self.hypotheticals.remove((node, j))
                    removes.add((node, j))
                elif (j, node) in self.hypotheticals:
                    self.graph.add_edge(j, node)
                    self.hypotheticals.remove((j, node))
                    removes.add((j, node))

            if nx.number_connected_components(self.graph) == DISTRICTS:
                # evaluate
                cand_scores = [objective(nx.connected_components(self.graph))
                               for objective in State.objectives]

                if self.dominated_by(cand_scores):
                    # print("Dominator found!", "old:", scores, "new:", cand_scores)
                    neighbors.append(State(self.graph.copy(), self.hypotheticals.copy(),
                                           cand_scores))

            self.hypotheticals = self.hypotheticals.union(removes).difference(adds)
            self.graph.add_edges_from(adds)
            self.graph.remove_edges_from(removes)

        return neighbors

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
    """Take a set of candidates and find dependencies."""
    # candidate x is dominated by candidates output[x]
    output = {i : set() for i in range(len(candidates))}
    for i, cand in enumerate(candidates):
        for j, o_cand in enumerate(candidates):
            if o_cand.dominated_by(cand.scores):
                output[j].add(i)
    return output

def draw_and_highlight(block_graph, *nodes):
    """Highlight a node."""
    index = lambda node: list(block_graph.nodes()).index(node)
    colors = ['r'] * len(block_graph)
    for i in nodes:
        colors[index(i)] = 'b'
    nx.draw_networkx(block_graph,
                     pos={node: list(data.get('shape').centroid.coords)[0] \
                          for node, data in block_graph.nodes(data=True)},
                     node_color=colors)
    plt.show()

@profile
def refine_and_optimize(candidate, block_graph, steps=1000, sample_size=1000):
    """Take a solution and return a nearby local maximum."""

    State.objectives = [objective(block_graph) for objective in OBJECTIVES]
    print("Finished generating objectives.")

    state = State.refine_candidate(candidate, block_graph)

    for _ in tqdm(range(steps), "Optimizing"):
        candidates = state.best_neighbors(sample_size)

        if not candidates:
            return state

        # candidates now contains every potential step
        # sort it into frontiers
        frontiers = list(toposort(to_input(candidates)))
        if not frontiers:
            pprint.pprint(candidates)

        # randomly choose something from the best frontier
        state = candidates[random.choice(tuple(frontiers[0]))]

    return state

@profile
def optimize(candidate, steps=1000, sample_size=1000):
    """Take a solution and return a nearby local maximum."""

    graph = candidate.reconstruct_graph()

    State.objectives = [objective(graph) for objective in OBJECTIVES]
    print("Finished generating objectives.")

    state = State(graph, candidate.hypotheticals, candidate.scores)

    for _ in tqdm(range(steps), "Optimizing"):
        candidates = state.best_neighbors(sample_size)

        if not candidates:
            return state

        # candidates now contains every potential step
        # sort it into frontiers
        frontiers = list(toposort(to_input(candidates)))
        if not frontiers:
            pprint.pprint(candidates)

        # randomly choose something from the best frontier
        state = candidates[random.choice(tuple(frontiers[0]))]

    return state

