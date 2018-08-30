from unittest import TestCase

import networkx as nx

from elbridge.evolution.hypotheticals import HypotheticalSet
from elbridge.utils import number_connected_components


class ConnectedComponentsTest(TestCase):
    def test_count_is_correct_if_no_edges_in_hypotheticals(self):
        graph = nx.path_graph(6)
        hypotheticals = HypotheticalSet(set())

        self.assertEqual(number_connected_components(graph, list(range(6)), hypotheticals), 1)

    def test_count_is_correct_with_edges_in_hypotheticals(self):
        graph = nx.path_graph(6)

        graph.remove_edge(2, 3)
        hypotheticals = HypotheticalSet({(2, 3)})

        self.assertEqual(number_connected_components(graph, list(range(6)), hypotheticals), 2)
        self.assertEqual(number_connected_components(graph, list(range(3)), hypotheticals), 1)
        self.assertEqual(number_connected_components(graph, list(range(4, 6)), hypotheticals), 1)




