from unittest import TestCase
from unittest.mock import Mock

import networkx as nx

from elbridge.evolution.chromosome import Chromosome
from elbridge.evolution.hypotheticals import HypotheticalSet
from elbridge.evolution.search_state import SearchState
from elbridge.xceptions import SameComponentException


class SearchStateTest(TestCase):
    def setUp(self):
        self.m_graph = nx.Graph()
        self.hypotheticals = HypotheticalSet(set())
        self.chromosome = Chromosome(nx.freeze(self.m_graph), [])
        SearchState.objectives = [Mock()]

    def test_dominates(self):
        s1 = SearchState(self.hypotheticals, self.chromosome, scores=[1, 1])
        s2 = SearchState(self.hypotheticals, self.chromosome, scores=[2, 1])
        self.assertTrue(s1.dominated_by(s2))
        self.assertFalse(s2.dominated_by(s1))

        s1 = SearchState(self.hypotheticals, self.chromosome, scores=[1, 1])
        s2 = SearchState(self.hypotheticals, self.chromosome, scores=[2, 2])
        self.assertTrue(s1.dominated_by(s2))
        self.assertFalse(s2.dominated_by(s1))

        s1 = SearchState(self.hypotheticals, self.chromosome, scores=[1, 1])
        s2 = SearchState(self.hypotheticals, self.chromosome, scores=[1, 1])
        self.assertFalse(s1.dominated_by(s2))
        self.assertFalse(s2.dominated_by(s1))

        s1 = SearchState(self.hypotheticals, self.chromosome, scores=[1, 2])
        s2 = SearchState(self.hypotheticals, self.chromosome, scores=[2, 1])
        self.assertFalse(s1.dominated_by(s2))
        self.assertFalse(s2.dominated_by(s1))

    def test_gradient(self):
        s1 = SearchState(self.hypotheticals, self.chromosome, scores=[1, 1])
        s2 = SearchState(self.hypotheticals, self.chromosome, scores=[2, 2])
        self.assertEqual(s1.gradient(s2), 2)
        self.assertEqual(s2.gradient(s1), -2)

        s1 = SearchState(self.hypotheticals, self.chromosome, scores=[1, 2])
        s2 = SearchState(self.hypotheticals, self.chromosome, scores=[2, 2])
        self.assertEqual(s1.gradient(s2), 1)
        self.assertEqual(s2.gradient(s1), -1)

        s1 = SearchState(self.hypotheticals, self.chromosome, scores=[1, 2])
        s2 = SearchState(self.hypotheticals, self.chromosome, scores=[2, 1])
        self.assertEqual(s1.gradient(s2), 0)
        self.assertEqual(s2.gradient(s1), 0)

    def test_connect_vertices_simple(self):
        # test on a path graph
        graph = nx.path_graph(4)
        graph.remove_edge(1, 2)
        hypotheticals = HypotheticalSet({(1, 2)})
        chromosome = Chromosome(nx.freeze(nx.path_graph(4)), [1, 1, 2, 2])

        state = SearchState(hypotheticals, chromosome, scores=[])
        state.connect_vertices(1, 2)

        self.assertEqual(state.hypotheticals, HypotheticalSet({(2, 3)}))
        self.assertEqual(state.chromosome.get_assignment(), [1, 1, 1, 2])

    def test_connect_vertices_repeated(self):
        # test on a path graph
        graph = nx.path_graph(4)
        graph.remove_edge(1, 2)
        hypotheticals = HypotheticalSet({(1, 2)})
        chromosome = Chromosome(nx.freeze(nx.path_graph(4)), [1, 1, 2, 2])

        state = SearchState(hypotheticals, chromosome, scores=[])
        state.connect_vertices(1, 2)
        state.connect_vertices(2, 3)

        self.assertEqual(state.hypotheticals, HypotheticalSet(set()))
        self.assertEqual(state.chromosome.get_assignment(), [1, 1, 1, 1])

    def test_connect_vertices_fails_if_same_component(self):
        with self.assertRaises(SameComponentException):
            SearchState(
                HypotheticalSet(set()), Chromosome(nx.freeze(nx.path_graph(4)), [1, 1, 1, 1]), scores=[]
            ).connect_vertices(2, 3)

    def test_connect_vertices_complex_graph(self):
        graph = nx.grid_graph([3, 2])
        nx.add_path(graph, [(2, i) for i in range(3)])
        hypotheticals = HypotheticalSet(set([((1, i), (2, i)) for i in range(3)]))
        chromosome = Chromosome(nx.freeze(nx.grid_graph([3, 3])), [1, 1, 1, 1, 1, 1, 2, 2, 2])

        state = SearchState(hypotheticals, chromosome, scores=[])

        state.connect_vertices((1, 1), (2, 1))
        self.assertEqual(
            state.hypotheticals, HypotheticalSet(
                {((1, 0), (2, 0)), ((1, 2), (2, 2)), ((2, 0), (2, 1)), ((2, 1), (2, 2))}
            )
        )
        self.assertEqual(state.chromosome.get_assignment(), [1, 1, 1, 1, 1, 1, 2, 1, 2])

        state.connect_vertices((2, 1), (2, 0))
        self.assertEqual(state.hypotheticals, HypotheticalSet({((1, 2), (2, 2)), ((2, 1), (2, 2))}))
        self.assertEqual(state.chromosome.get_assignment(), [1, 1, 1, 1, 1, 1, 1, 1, 2])

        state.connect_vertices((2, 1), (2, 2))
        self.assertEqual(state.hypotheticals, HypotheticalSet(set()))
        self.assertEqual(state.chromosome.get_assignment(), [1, 1, 1, 1, 1, 1, 1, 1, 1])
