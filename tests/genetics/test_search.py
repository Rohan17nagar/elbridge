import random
from unittest import TestCase
from unittest.mock import patch

import matplotlib.pyplot as plt
import networkx as nx

from elbridge.evolution.chromosome import Chromosome
from elbridge.evolution.objectives import PopulationEquality
from elbridge.evolution.search import find_best_neighbor, optimize


class SearchTest(TestCase):
    def setUp(self):
        self.master_graph = nx.Graph()
        nx.add_path(self.master_graph, [0, 1, 2])
        nx.add_path(self.master_graph, [5, 6, 7])
        nx.add_path(self.master_graph, [2, 3, 4, 5])
        self.master_graph.graph['order'] = {i: i for i in range(8)}
        nx.set_node_attributes(self.master_graph, {i: 1 for i in self.master_graph}, name='pop')
        self.master_graph = nx.freeze(self.master_graph)

        Chromosome.objectives = [PopulationEquality(self.master_graph, districts=2)]

        self.m_tqdm_patch = patch('elbridge.evolution.search.tqdm')
        self.m_tqdm = self.m_tqdm_patch.start()
        self.m_tqdm.side_effect = lambda x, *y, **z: x

    def tearDown(self):
        self.m_tqdm_patch.stop()

    def test_find_best_neighbor_simple(self):
        master_graph = nx.path_graph(6)
        nx.set_node_attributes(master_graph, {i: 1 for i in master_graph}, name='pop')
        master_graph = nx.freeze(master_graph)
        Chromosome.objectives = [PopulationEquality(master_graph, districts=2)]

        s1 = Chromosome(master_graph, [1, 1, 2, 2, 2, 2])
        s2 = find_best_neighbor(s1)

        self.assertEqual(s2.get_scores(), [0.0])
        self.assertEqual(s2.get_assignment(), [1, 1, 1, 2, 2, 2])

        s3 = find_best_neighbor(s2)
        self.assertIsNone(s3)

    def test_optimize_simple(self):
        master_graph = nx.path_graph(6)
        nx.set_node_attributes(master_graph, {i: 1 for i in master_graph}, name='pop')
        Chromosome.objectives = [PopulationEquality(master_graph, districts=2)]

        chromosome = Chromosome(master_graph, [1, 2, 2, 2, 2, 2])
        best_state = optimize(chromosome)

        self.assertEqual(best_state.get_scores(), [0.0])
        self.assertEqual(best_state.get_assignment(), [1, 1, 1, 2, 2, 2])


class SearchLoadTest(TestCase):
    def tearDown(self):
        plt.close('all')

    def test_find_best_neighbor_complex(self):
        size = 1000

        master_graph = nx.path_graph(size)

        nx.set_node_attributes(master_graph, {i: 1 for i in range(2)}, name='pop')
        nx.set_node_attributes(master_graph, {i: 2 for i in range(2, size)}, name='pop')
        Chromosome.objectives = [PopulationEquality(master_graph, districts=size - 1)]
        chromosome = Chromosome(master_graph, list(range(size)))

        new_chromosome = find_best_neighbor(chromosome, sample_size=size * 2)

        self.assertEqual(new_chromosome.get_scores(), [0])
        self.assertEqual(new_chromosome.get_assignment(), [1, 1] + list(range(2, size)))

    def test_optimize_moderately_complex(self):
        grid_size = [32, 32]
        node_count = grid_size[0] * grid_size[1]
        edge_count = (grid_size[0] - 1) * grid_size[1] + grid_size[0] * (grid_size[1] - 1)

        districts = 2
        assignment = random.choices(range(1, districts + 1), k=node_count)

        master_graph = nx.grid_graph(grid_size)
        nx.set_node_attributes(master_graph, {i: 1 for i in master_graph}, name='pop')
        Chromosome.objectives = [PopulationEquality(master_graph, districts=districts)]
        chromosome = Chromosome(master_graph, assignment)

        best_state = optimize(chromosome, sample_size=edge_count * 2)
        print("Original scores: {}".format(chromosome.get_scores()))
        print("Final scores: {}".format(best_state.get_scores()))
        self.assertTrue(best_state.dominates(chromosome))

        better_state = optimize(best_state, sample_size=edge_count * 2)
        best_state.normalize()
        better_state.normalize()
        self.assertEqual(best_state, better_state)

