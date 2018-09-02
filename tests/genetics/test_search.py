import gc
from unittest import TestCase
from unittest.mock import patch

import networkx as nx
import objgraph

from elbridge.evolution.chromosome import Chromosome
from elbridge.evolution.objectives import PopulationEquality
from elbridge.evolution.search import make_step, find_best_neighbor, optimize
from elbridge.evolution.search_state import SearchState


class SearchTest(TestCase):
    def setUp(self):
        self.master_graph = nx.Graph()
        nx.add_path(self.master_graph, [0, 1, 2])
        nx.add_path(self.master_graph, [5, 6, 7])
        nx.add_path(self.master_graph, [2, 3, 4, 5])
        self.master_graph.graph['order'] = {i: i for i in range(8)}
        nx.set_node_attributes(self.master_graph, {i: 1 for i in self.master_graph}, name='pop')
        self.master_graph = nx.freeze(self.master_graph)

        SearchState.objectives = [PopulationEquality(self.master_graph, districts=2)]

    def test_make_step_returns_better_step_for_better_move(self):
        s1 = SearchState(Chromosome(self.master_graph, [1, 1, 1, 1, 1, 2, 2, 2]))
        s1.evaluate()
        s2 = make_step(s1, (5, 4))

        self.assertEqual(s2, SearchState(
            Chromosome(self.master_graph, [1, 1, 1, 1, 2, 2, 2, 2])
        ))

    def test_make_step_returns_none_for_worse_move(self):
        s1 = SearchState(Chromosome(self.master_graph, [1, 1, 1, 1, 2, 2, 2, 2]))
        s1.evaluate()

        s2 = make_step(s1, (3, 4))
        self.assertIsNone(s2)

    def test_find_best_neighbor_simple(self):
        master_graph = nx.path_graph(6)
        nx.set_node_attributes(master_graph, {i: 1 for i in master_graph}, name='pop')
        master_graph = nx.freeze(master_graph)
        chromosome = Chromosome(master_graph, [1, 1, 2, 2, 2, 2])

        SearchState.objectives = [PopulationEquality(master_graph, districts=2)]
        s1 = SearchState(chromosome)
        s1.evaluate()

        s2 = find_best_neighbor(s1)

        self.assertEqual(s2.scores, [3.0])
        self.assertEqual(s2.chromosome.get_assignment(), [1, 1, 1, 2, 2, 2])

        s3 = find_best_neighbor(s2)
        self.assertIsNone(s3)

    def test_find_best_neighbor_complex(self):
        size = 1000

        master_graph = nx.path_graph(size)

        nx.set_node_attributes(master_graph, {i: 1 for i in range(2)}, name='pop')
        nx.set_node_attributes(master_graph, {i: 2 for i in range(2, size)}, name='pop')
        chromosome = Chromosome(master_graph, list(range(size)))

        SearchState.objectives = [PopulationEquality(master_graph, districts=size - 1)]
        s1 = SearchState(chromosome)
        s1.evaluate()

        s2 = find_best_neighbor(s1, sample_size=size * 2)

        self.assertEqual(s2.scores, [2.0])
        self.assertEqual(s2.chromosome.get_assignment(), [1, 1] + list(range(2, size)))

    @patch('elbridge.evolution.search.tqdm')
    def test_optimize_simple(self, m_tqdm):
        m_tqdm.side_effect = lambda x, *y, **z: x

        master_graph = nx.path_graph(6)
        nx.set_node_attributes(master_graph, {i: 1 for i in master_graph}, name='pop')
        master_graph = nx.freeze(master_graph)

        chromosome = Chromosome(master_graph, [1, 2, 2, 2, 2, 2])

        SearchState.objectives = [PopulationEquality(master_graph, districts=2)]

        best_state = optimize(chromosome)

        self.assertEqual(best_state.scores, [3.0])
        self.assertEqual(best_state.chromosome.get_assignment(), [1, 1, 1, 2, 2, 2])

    def test_optimize_moderately_complex(self):
        grid_size = [20, 20]
        node_count = grid_size[0] * grid_size[1]

        master_graph = nx.grid_graph(grid_size)
        nx.set_node_attributes(master_graph, {i: 1 for i in master_graph}, name='pop')
        master_graph = nx.freeze(master_graph)
        chromosome = Chromosome(master_graph, list(range(1, node_count + 1)))

        SearchState.objectives = [PopulationEquality(master_graph, districts=2)]

        best_state = optimize(chromosome)
        self.assertEqual(best_state.scores, [node_count // 2])
