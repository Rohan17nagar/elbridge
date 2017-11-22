"""Objective functions. These functions take a chromosome and return a value, such that better 
chromosomes have higher values."""

import statistics
import networkx as nx

DISTRICTS = 3

class PopulationEquality():
    # pylint: disable=R0903
    """Test population equality."""
    def __init__(self, graph):
        self.total_pop = sum([data.get('pop', 0) for _, data in
                              graph.nodes(data=True)])
        self.min_value = 0
        self.max_value = self.total_pop / DISTRICTS

    def __repr__(self):
        return "Population equality"

    def __call__(self, components):
        """Returns the mean absolute deviation of subgraph population."""
        return min([sum([data.get('pop') for _, data in component])
                    for component in components])

class SizeEquality():
    # pylint: disable=R0903
    """Test size equality. For testing purposes only"""
    def __init__(self, graph):
        self.total_pop = len(graph)
        self.min_value = 0
        self.max_value = self.total_pop / DISTRICTS

    def __repr__(self):
        return "Size equality"

    def __call__(self, components):
        """Returns the mean absolute deviation of subgraph population."""
        return min(map(len, components))

OBJECTIVES = [PopulationEquality]
