from itertools import product
from unittest import TestCase

import matplotlib.pyplot as plt
import networkx as nx

from elbridge.evolution.candidate import Candidate
from elbridge.evolution import objectives
from elbridge.evolution.chromosome import Chromosome
from elbridge.evolution.search import SearchState


class CandidateTest(TestCase):
    def _create_graph(self, graph):
        self.graph = graph
        self.objectives = [objectives.PopulationEquality(self.graph)]

        Candidate.master_graph = self.graph
        Candidate.mutation_probability = -1
        Candidate.objectives = self.objectives

        SearchState.master_graph = self.graph
        SearchState.objectives = self.objectives

    def test_create_candidate(self):
        G = nx.OrderedGraph(nx.grid_graph([5, 3]))
        m = {
            (i, j): 3*i + j + 1 for i, j in product(range(3), range(5))
        }
        G.graph['order'] = {vertex: idx for idx, vertex in enumerate(G)}
        nx.set_node_attributes(G, m, name='pop')
        self._create_graph(G)

        print(list(enumerate(G)))

        d = Candidate(Chromosome(
            self.graph, [1, 1, 2, 3, 4,
                         4, 5, 4, 4, 4,
                         5, 5, 2, 2, 4]
        ))
        nx.draw_networkx(d.graph, pos={n: n for n in G.nodes()})
        plt.show()

        print("d starting chromosome", d.chromosome, d.scores)
        do = d.optimize()
        print("d ending chromosome", do.chromosome, do.scores)
        nx.draw_networkx(do.graph, pos={n: n for n in G.nodes()})
        plt.show()
