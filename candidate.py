# pylint: disable=C0103
"""Encapsulates a candidate solution."""

import random

from disjointset import DisjointSet
import objectives
import shape
import search

import networkx as nx

class Candidate():
    # pylint: disable=R0902
    """
    Encapsulates a candidate solution.

    The chromosome is given by an |E|-length real array A, where A[i] is the order in which edge i 
    is added to the graph.

    The Candidate class *must* be "initialized" first by assigning a global master graph and a 
    global mutation probability.
    """
    i = 0
    
    master_graph = nx.Graph()
    mutation_probability = None
    objectives = []

    def __init__(self, edge_set, copy=False):
        if not Candidate.master_graph or not Candidate.mutation_probability \
           or not Candidate.objectives:
            raise Exception("Class Candidate hasn't been implemented yet!")

        self.chromosome = edge_set

        # set of candidates this candidate dominates
        self.dominated_set = set()
        # number of candidates this candidate is dominated by
        self.domination_count = 0
        # this candidate's front
        self.rank = 0
        # distance to other candidates on front
        self.distance = 0

        self.mutation_probability = Candidate.mutation_probability

        self.graph = None
        self.hypotheticals = set()
        self.components = []

        if copy:
            self.scores = []
            self.name = None
        else:
            self.reconstruct_graph()
            assert self.components
            self.scores = [objective(self.components)
                           for objective in Candidate.objectives]
            self.name = Candidate.i
            Candidate.i += 1

    def __repr__(self):
        return str(self.name) + " (" + str(self.scores) + ")"

    def __eq__(self, other):
        self.reconstruct_graph()
        other.reconstruct_graph()

        return self.components == other.components

    def copy(self):
        """Returns a copy of this chromosome."""
        copy = Candidate(self.chromosome, copy=True)
        copy.scores = self.scores
        copy.name = self.name
        copy.graph = self.graph
        return copy

    def dominates(self, other):
        """
        Returns True if p dominates q.

        Domination is defined as a partial ordering < on solutions, where
        for some objectives f1, f2, ..., fm, p < q iff for all i <= m fi(p) >= fi(q).
        """
        as_good = True
        better = False
        for i in range(len(self.scores)):
            if self.scores[i] < other.scores[i]:
                as_good = False
                break
            if self.scores[i] > other.scores[i]:
                better = True

        return as_good and better

    def crossover(self, other):
        """
        Return new Candidate objects.
        """
        # pick a random number in [0,|E|)
        split_point = random.randint(0, len(self.chromosome))

        chromosome_a = self.chromosome[:split_point] + other.chromosome[split_point:]
        chromosome_b = other.chromosome[:split_point] + self.chromosome[split_point:]

        return [Candidate(chromosome_a), Candidate(chromosome_b)]

    def mutate(self):
        """Mutate a Candidate solution in place."""
        if random.random() < self.mutation_probability:
            element = random.randint(0, len(self.chromosome)-1)
            self.chromosome[element] = random.random()

        # for idx in range(len(self.chromosome)):
            # if random.random() < self.mutation_probability:
                # self.chromosome[idx] = random.random()

    # @profile
    def reconstruct_graph(self):
        """Take a chromosome and return the corresponding graph.

        chromosome[i] corresponds to the priority of edge i.
        """
        if self.graph:
            return self.graph

        master = Candidate.master_graph
        order = sorted([(priority, idx) for idx, priority in enumerate(self.chromosome)],
                       reverse=True)
        disjoint_set = DisjointSet(master.nodes())

        H = nx.Graph()
        H.add_nodes_from(master.nodes(data=True))
        i = 0

        hypotheticals = set(master.edges())
        edge_list = list(master.edges())

        for _, i in order:
            u, v = edge_list[i]
            # if disjoint_set.find(u) == disjoint_set.find(v):
                # this is a move that wouldn't have any effect
                # continue
            hypotheticals.remove((u, v))
            H.add_edge(u, v)
            disjoint_set.union(u, v)

            if len(disjoint_set) == objectives.DISTRICTS:
                break

        components = disjoint_set.get_sets()
        self.components = [[(n, master.node[n]) for n in component]
                           for component in components]

        for component in components:
            original_subgraph = master.subgraph(component)
            for edge in original_subgraph.edges():
                if not H.has_edge(*edge):
                    # this is an edge in the original inside a component
                    H.add_edge(*edge)
                    hypotheticals.remove(edge)

        self.hypotheticals = hypotheticals

        assert len(disjoint_set) == objectives.DISTRICTS, disjoint_set

        self.graph = H
        return H

    def plot(self, save=False):
        """Plots a chromosome."""
        graph = self.reconstruct_graph()
        title = "Chromosome (" \
                + "; ".join(["{name}: {value}"
                             .format(name=str(Candidate.objectives[idx]), value=self.scores[idx])
                             for idx in range(len(Candidate.objectives))]) + ")"
        shapes = []

        print("Goal size:", sum([data.get('pop')
                                 for _, data in graph.nodes(data=True)])/objectives.DISTRICTS)

        for i, component in enumerate(nx.connected_component_subgraphs(graph)):
            color = (random.random(), random.random(), random.random())
            shapes += [(data.get('shape'), color) for _, data in component.nodes(data=True)]

            print("Component", i)
            """print("\n".join(["\tCounty {name}: population {pop}"
                             .format(name=node, pop=data.get('pop'))
                             for node, data in component.nodes(data=True)]))"""
            print("Total population:",
                  sum([data.get('pop', 0) for _, data in component.nodes(data=True)]))
            print()

        shape.plot_shapes(shapes, title=title, save=save)

def test():
    import matplotlib.pyplot as plt
    G = nx.path_graph(10)
    Candidate.master_graph = G
    Candidate.objectives = [objectives.SizeEquality(G)]
    Candidate.mutation_probability = -1

    a = Candidate([3, 1, 2, 5, 6, 0, 7, 8, 4])
    b = Candidate([0, 1, 2, 3, 4, 5, 6, 7, 8])

    g_a = a.reconstruct_graph()
    g_b = b.reconstruct_graph()
    print(a.chromosome, b.chromosome)

    print("a scores", a.scores)
    print("b scores", b.scores)
    nx.draw_networkx(g_a)
    plt.show()

    nx.draw_networkx(g_b)
    plt.show()

    [c, d] = a.crossover(b)
    print(c.chromosome, d.chromosome)

    print("c scores", c.scores)
    print("d scores", d.scores)

    g_c = c.reconstruct_graph()
    g_d = d.reconstruct_graph()

    nx.draw_networkx(g_c)
    plt.show()

    nx.draw_networkx(g_d)
    plt.show()


if __name__ == "__main__":
    test()


