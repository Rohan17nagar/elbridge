from itertools import product
from unittest import TestCase

import networkx as nx

from elbridge.evolution.chromosome import Chromosome
from elbridge.evolution.objectives import PopulationEquality
from elbridge.utilities.xceptions import SameComponentException


class ChromosomeTest(TestCase):
    def setUp(self):
        self.simple_graph = nx.path_graph(4)
        nx.set_node_attributes(self.simple_graph, {i: 1 for i in range(4)}, name='pop')
        Chromosome.objectives = [PopulationEquality(self.simple_graph, districts=2)]

    def test_create_simple_chromosome(self):
        chromosome = Chromosome(self.simple_graph, [1, 1, 2, 2])
        self.assertEqual(chromosome.get_assignment(), [1, 1, 2, 2])
        self.assertEqual(chromosome.get_components(), {1: {0, 1}, 2: {2, 3}})
        self.assertEqual(chromosome.get_component_scores(), {
            1: {'total_pop': 2, 'components': 1},
            2: {'total_pop': 2, 'components': 1},
        })
        self.assertEqual(chromosome.get_hypotheticals().edges, {(1, 2), (2, 1)})

    def test_connect_vertices_simple(self):
        # test on a path graph
        chromosome = Chromosome(self.simple_graph, [1, 1, 2, 2])

        new_chromosome = chromosome.connect_vertices((1, 2))
        self.assertEqual(new_chromosome.get_assignment(), [1, 1, 1, 2])
        self.assertEqual(new_chromosome.get_components(), {1: {0, 1, 2}, 2: {3}})
        self.assertEqual(new_chromosome.get_component_scores(), {
            1: {'total_pop': 3, 'components': 1},
            2: {'total_pop': 1, 'components': 1},
        })

    def test_connect_vertices_repeated(self):
        # test on a path graph
        chromosome = Chromosome(self.simple_graph, [1, 1, 2, 2])

        new_chromosome = chromosome.connect_vertices((1, 2)).connect_vertices((2, 3))

        self.assertEqual(new_chromosome.get_assignment(), [1, 1, 1, 1])
        self.assertEqual(new_chromosome.get_components(), {1: {0, 1, 2, 3}})
        self.assertEqual(new_chromosome.get_component_scores(), {
            1: {'total_pop': 4, 'components': 1},
        })

    def test_connect_vertices_fails_if_same_component(self):
        with self.assertRaises(SameComponentException):
            Chromosome(self.simple_graph, [1, 1, 1, 1]).connect_vertices((2, 3))

    def test_connect_vertices_complex_graph(self):
        graph = nx.grid_graph([3, 3])
        nx.set_node_attributes(graph, {i: 1 for i in graph}, name='pop')
        Chromosome.objectives = [PopulationEquality(graph, districts=2)]

        chromosome = Chromosome(graph, [1, 1, 1, 1, 1, 1, 2, 2, 2])

        chromosome = chromosome.connect_vertices(((1, 1), (2, 1)))
        self.assertEqual(chromosome.get_assignment(), [1, 1, 1, 1, 1, 1, 2, 1, 2])

        chromosome = chromosome.connect_vertices(((2, 1), (2, 0)))
        self.assertEqual(chromosome.get_assignment(), [1, 1, 1, 1, 1, 1, 1, 1, 2])

        chromosome = chromosome.connect_vertices(((2, 1), (2, 2)))
        self.assertEqual(chromosome.get_assignment(), [1, 1, 1, 1, 1, 1, 1, 1, 1])
