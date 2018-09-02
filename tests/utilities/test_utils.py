from unittest import TestCase

import networkx as nx

from elbridge.evolution.chromosome import Chromosome
from elbridge.utilities.utils import number_connected_components


class ConnectedComponentsTest(TestCase):
    def test_count_is_correct_for_everything_in_one_component(self):
        graph = nx.path_graph(6)
        chromosome = Chromosome(graph, [1, 1, 1, 1, 1, 1])

        self.assertEqual(number_connected_components(list(range(6)), chromosome), 1)

    def test_count_is_correct_with_edges_in_hypotheticals(self):
        chromosome = Chromosome(nx.path_graph(6), [1, 1, 1, 2, 2, 2])

        self.assertEqual(number_connected_components(list(range(6)), chromosome), 2)
        self.assertEqual(number_connected_components(list(range(3)), chromosome), 1)
        self.assertEqual(number_connected_components(list(range(4, 6)), chromosome), 1)

    def test_count_is_correct_for_point_graph(self):
        graph = nx.Graph()
        graph.add_nodes_from(range(10))
        graph.add_edge(0, 1)
        chromosome = Chromosome(graph, [1, 1, 2, 2, 2, 2, 2, 2, 2])

        self.assertEqual(number_connected_components(list(range(10)), chromosome), 9)
        self.assertEqual(number_connected_components(list(range(2)), chromosome), 1)
        for i in range(3, 10):
            self.assertEqual(number_connected_components([i], chromosome), 1)





