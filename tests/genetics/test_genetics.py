import random
from unittest import TestCase

import networkx as nx
from shapely.geometry import box

from elbridge.evolution import genetics
from elbridge.evolution.candidate import Candidate
from elbridge.evolution.chromosome import Chromosome
from elbridge.evolution.objectives import PopulationEquality


class GeneticsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master_graph = nx.cycle_graph(10)
        cls.master_graph.graph['districts'] = 2
        nx.set_node_attributes(cls.master_graph, {i: 1 for i in cls.master_graph}, name='pop')
        Chromosome.objectives = [
            PopulationEquality(cls.master_graph)
        ]

    def test_sorting_on_simple_population(self):
        population = map(Candidate, [
            Chromosome(self.master_graph, [1, 1, 1, 1, 1, 2, 2, 2, 2, 2]),
            Chromosome(self.master_graph, [1, 2, 1, 2, 1, 2, 1, 2, 1, 2]),
            Chromosome(self.master_graph, [1, 1, 1, 2, 2, 2, 1, 1, 1, 2]),
        ])

        frontiers = genetics.fast_non_dominated_sort(list(population))
        self.assertListEqual(frontiers, [
            [Candidate(Chromosome(self.master_graph, [1, 1, 1, 1, 1, 2, 2, 2, 2, 2]))],
            [Candidate(Chromosome(self.master_graph, [1, 1, 1, 2, 2, 2, 1, 1, 1, 2]))],
            [Candidate(Chromosome(self.master_graph, [1, 2, 1, 2, 1, 2, 1, 2, 1, 2]))]
        ])

    def test_sorting_on_equal_population(self):
        population = map(Candidate, [
            Chromosome(self.master_graph, [1, 1, 1, 1, 1, 2, 2, 2, 2, 2]),
            Chromosome(self.master_graph, [1, 1, 1, 1, 1, 2, 2, 2, 2, 2]),
            Chromosome(self.master_graph, [1, 1, 1, 1, 1, 2, 2, 2, 2, 2]),
        ])

        frontiers = genetics.fast_non_dominated_sort(list(population))
        self.assertListEqual(frontiers, [[
            Candidate(Chromosome(self.master_graph, [1, 1, 1, 1, 1, 2, 2, 2, 2, 2])),
            Candidate(Chromosome(self.master_graph, [1, 1, 1, 1, 1, 2, 2, 2, 2, 2])),
            Candidate(Chromosome(self.master_graph, [1, 1, 1, 1, 1, 2, 2, 2, 2, 2])),
        ]])


class GeneticsLoadTest(TestCase):
    def test_nsga2_simple(self):
        size = 14
        master_graph = nx.grid_graph([size, size])
        master_graph.graph['districts'] = 2
        nx.set_node_attributes(master_graph, {i: 1 for i in master_graph}, name='pop')
        nx.set_node_attributes(master_graph, {(i, j): box(i, j, i+1, j+1) for (i, j) in master_graph}, name='shape')

        frontier, data = genetics.run_nsga2(
            master_graph, [PopulationEquality(master_graph)], multiprocess=False, max_generations=100, pop_size=500,
            optimize=False
        )

        for gen_id in data:
            if gen_id % 20 != 0:
                continue
            gen_data = data[gen_id]
            random_pareto: Candidate = random.choice(gen_data.get('pareto_frontier'))
            random_pareto.plot()

        print("\n".join("{}".format(i.chromosome.get_component_scores()) for i in frontier))
