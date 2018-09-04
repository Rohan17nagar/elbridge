from unittest import TestCase

import networkx as nx

from elbridge.utilities.utils import dominates, gradient, number_connected_components


class UtilsTest(TestCase):
    def test_dominates(self):
        s1 = [1, 1]
        s2 = [2, 1]
        self.assertTrue(dominates(s2, s1))
        self.assertFalse(dominates(s1, s2))

        s1 = [1, 1]
        s2 = [2, 2]
        self.assertTrue(dominates(s2, s1))
        self.assertFalse(dominates(s1, s2))

        s1 = [1, 1]
        s2 = [1, 1]
        self.assertFalse(dominates(s2, s1))
        self.assertFalse(dominates(s1, s2))

        s1 = [1, 2]
        s2 = [2, 1]
        self.assertFalse(dominates(s2, s1))
        self.assertFalse(dominates(s1, s2))

    def test_gradient(self):
        s1 = [1, 1]
        s2 = [2, 2]
        self.assertEqual(gradient(s2, s1), 2)
        self.assertEqual(gradient(s1, s2), -2)

        s1 = [1, 2]
        s2 = [2, 2]
        self.assertEqual(gradient(s2, s1), 1)
        self.assertEqual(gradient(s1, s2), -1)

        s1 = [1, 2]
        s2 = [2, 1]
        self.assertEqual(gradient(s2, s1), 0)
        self.assertEqual(gradient(s1, s2), 0)

    def test_ncc(self):
        graph = nx.path_graph(10)
        graph.remove_edge(4, 5)

        self.assertEqual(number_connected_components(graph, set(range(10))), 2)
        self.assertEqual(number_connected_components(graph, set(range(5))), 1)
        self.assertEqual(number_connected_components(graph, set(range(5, 10))), 1)
