# pylint: disable=C0103
"""Encapsulates a candidate solution."""

import random

import objectives
import shape
import search
import utils

import networkx as nx

class Candidate():
    # pylint: disable=R0902
    """
    Encapsulates a candidate solution.

    The chromosome is given by an |E|-length real array A, where A[i] is the order in which edge i
    is added to the graph.

    The Candidate class *must* be "initialized" first by assigning a global
    master graph and a global mutation probability.
    """
    i = 0
    master_graph = nx.Graph()
    mutation_probability = None
    objectives = []
    cache = {}

    @profile
    def __init__(self, vertex_set, fr=False):
        if not Candidate.master_graph or not Candidate.mutation_probability \
           or not Candidate.objectives:
            raise Exception("Class Candidate hasn't been implemented yet!")

        # |V|-length array where vs[i] = j means that vertex i is in district j
        self.chromosome = vertex_set

        # normalize: components are indexed by their appearance order in
        # chromosome
        mapping = {}
        ind = 1
        for idx in range(len(self.chromosome)):
            cur_comp = self.chromosome[idx]
            if cur_comp not in mapping:
                mapping[cur_comp] = ind
                ind += 1
            self.chromosome[idx] = mapping.get(cur_comp)

        vertex_str = "".join(map(str, vertex_set))
        if vertex_str in Candidate.cache:
            pass

        # set of candidates this candidate dominates
        self.dominated_set = set()
        # number of candidates this candidate is dominated by
        self.domination_count = 0
        # this candidate's front
        self.rank = 0
        # distance to other candidates on front
        self.distance = 0

        self.graph = None
        self.hypotheticals = set()

        component_map = utils.chromosome_to_components(Candidate.master_graph,
                                                       self.chromosome)
        self.components = list(component_map.values())
        self.name = None

        self.reconstruct_graph(force_reconstruct=fr)
        self.scores = [objective(self.components, self.graph)
                       for objective in Candidate.objectives]
        self.name = Candidate.i
        Candidate.i += 1

        Candidate.cache[vertex_str] = self

    def __repr__(self):
        return str(self.name) + " (" + str(self.scores) + ")"

    def __eq__(self, other):
        return self.chromosome == other.chromosome

    def __hash__(self):
        return tuple(self.chromosome).__hash__()

    def refresh(self):
        """Clear out NSGA stuff."""
        # set of candidates this candidate dominates
        self.dominated_set = set()
        # number of candidates this candidate is dominated by
        self.domination_count = 0
        # this candidate's front
        self.rank = 0
        # distance to other candidates on front
        self.distance = 0

    @staticmethod
    def generate():
        """Create a new random candidate."""
        graph = Candidate.master_graph
        assignment = [random.randint(1, objectives.DISTRICTS) for i in
                      range(len(graph))]
        return Candidate(assignment)

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

    def crossover_and_mutate(self, other):
        """
        Return new Candidate objects.
        """
        # pick a random number in [1,|V|)
        split_point = random.randint(1, len(self.chromosome)-1)

        chromosome_a = self.chromosome[:split_point] + other.chromosome[split_point:]
        chromosome_b = other.chromosome[:split_point] + self.chromosome[split_point:]

        cands = [chromosome_a, chromosome_b]
        out = []
        for child in cands:
            if random.random() < Candidate.mutation_probability:
                element = random.randint(0, len(child) - 1)
                child[element] = random.randint(1, objectives.DISTRICTS)
            out.append(Candidate(child))
        return out

    @profile
    def reconstruct_graph(self, force_reconstruct=False):
        """Take a chromosome and return the corresponding graph.

        chromosome[i] corresponds to the connected component of vertex i.
        """
        if not force_reconstruct and self.graph:
            return self.graph

        master = Candidate.master_graph
        H = nx.Graph(master)
        H.add_nodes_from(master.nodes(data=True))
        H.graph['order'] = master.graph['order']
        self.hypotheticals = set()

        for i, j in master.edges():
            if utils.get_component(self.chromosome, master, i) \
               != utils.get_component(self.chromosome, master, j):
                H.remove_edge(i, j)
                self.hypotheticals.add((i, j))

        self.graph = H
        return H

    def plot(self, save=False):
        """Plots a chromosome."""
        graph = self.reconstruct_graph()
        output = ""
        title = "Chromosome (" \
                + "; ".join(["{name}: {value}"
                             .format(name=str(Candidate.objectives[idx]), value=self.scores[idx])
                             for idx in range(len(Candidate.objectives))]) + ")"
        output += title + "\n"
        shapes = []

        output += "Goal size: " + str(sum([data.get('pop') for _, data in graph.nodes(data=True)])
                                      / objectives.DISTRICTS)
        output += "\n"

        for i, component in enumerate(nx.connected_component_subgraphs(graph)):
            color = (random.random(), random.random(), random.random())
            shapes += [(data.get('shape'), color) for _, data in component.nodes(data=True)]

            output += "Component " + str(i) + ":\n"
            output += "Total population: " +  \
                  str(sum([data.get('pop', 0) for _, data in
                           component.nodes(data=True)]))
            output += "\n\n"

        if save:
            with open(title + '.out.txt', 'w+') as outfile:
                outfile.write(output)
        else:
            print(output)

        shape.plot_shapes(shapes, title=title, save=save)

    def optimize(self):
        """Convert a candidate into a state, optimize, and convert back."""
        state = search.optimize(self, steps=20, sample_size=50)
        out = Candidate(state.chromosome, fr=True)

        if not out.scores == state.scores:
            print("inconsistency found between search state and candidate")
            print("O score", self.scores)
            print("S score", state.scores)
            print("C score", out.scores)

            print("O chromosome", self.chromosome)
            print("S chromosome", state.chromosome)
            print("C chromosome", out.chromosome)

            o_graph = self.reconstruct_graph()
            s_graph = state.graph
            c_graph = out.reconstruct_graph()

            print("O components", list(nx.connected_components(o_graph)))
            print("S components", list(nx.connected_components(s_graph)))
            print("C components", list(nx.connected_components(c_graph)))

            assert False
        return out

def test():
    """Testing function."""
    import matplotlib.pyplot as plt
    G = nx.OrderedGraph()
    G.add_nodes_from([(i, j) for i in range(5) for j in range(3)])
    for i in range(5):
        for j in range(3):
            if j < 2:
                G.add_edge((i, j), (i, j+1))
            if i < 4:
                G.add_edge((i, j), (i+1, j))
    m = {}
    for i in range(5):
        for j in range(3):
            m[(i, j)] = 3*i + j + 1
    nx.set_node_attributes(G, m, name='pop')
    Candidate.master_graph = G
    Candidate.objectives = [objectives.PopulationEquality(G)]
    Candidate.mutation_probability = -1
    # nx.draw_networkx(G, pos={n : n for n in G.nodes()})
    # plt.show()

    # a = Candidate([1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5])
    # b = Candidate([1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5])

    # print(a.chromosome, b.chromosome)

    # print("a scores", a.scores)
    # print("b scores", b.scores)

    # g_a = a.reconstruct_graph()
    # g_b = b.reconstruct_graph()

    # c = Candidate([5, 5, 5, 4, 4, 4, 3, 3, 3, 2, 2, 2, 1, 1, 1])
    # assert c.chromosome == [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5]

    d = Candidate([1, 1, 2, 3, 4, 4, 5, 4, 4, 5, 2, 4, 2, 2, 4])
    nx.draw_networkx(d.reconstruct_graph(), pos={n: n for n in G.nodes()})
    plt.show()

    print("d starting chromosome", d.chromosome, d.scores)
    do = d.optimize()
    print("d ending chromosome", do.chromosome, do.scores)
    nx.draw_networkx(do.reconstruct_graph(), pos={n: n for n in G.nodes()})
    plt.show()

if __name__ == "__main__":
    test()

