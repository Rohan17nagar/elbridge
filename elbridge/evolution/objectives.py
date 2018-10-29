"""Objective functions. These functions take a chromosome and return a value, such that better 
chromosomes have higher values."""

from typing import Dict, List

from elbridge.evolution.chromosome import Chromosome


class ObjectiveFunction:
    key = None
    min_value = None
    max_value = None
    goal_value = None

    def __call__(self, chromosome: Chromosome) -> float:
        pass


class PopulationEquality(ObjectiveFunction):
    """Test population equality."""

    def __init__(self, master_graph, key='pop'):
        self.key = key
        self.districts = master_graph.graph['districts']

        self.total_pop = sum([data.get(self.key, 0) for _, data in master_graph.nodes(data=True)])
        self.min_value = -1 * (self.total_pop - self.districts)
        self.max_value = 0

        self.goal_value = self.max_value

    def __repr__(self):
        return "Population equality"

    def __call__(self, chromosome: Chromosome) -> float:
        """
        Returns the score of the given components.
        """
        component_scores: List[Dict[str, float]] = chromosome.get_component_scores().values()

        min_pop: float = min(score['total_pop'] for score in component_scores)
        max_pop: float = max(score['total_pop'] for score in component_scores)
        num_components: int = sum(score['components'] for score in component_scores)

        _mp_score: float = max_pop - min_pop
        _sd_score: int = num_components - self.districts
        _dc_score: int = abs(len(component_scores) - self.districts)

        return -1 * (_mp_score + 100 * _sd_score + 1000 * _dc_score)
