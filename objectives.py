"""Objective functions. These functions take a chromosome and return a value, such that better 
chromosomes have higher values."""

import statistics
import networkx as nx

DISTRICTS = 20

class PopulationEquality():
    # pylint: disable=R0903
    """Test population equality."""
    def __init__(self, graph):
        self.total_pop = sum([data.get('pop', 0) for _, data in
                              graph.nodes(data=True)])
        self.max_value = statistics.stdev([0] * (len(graph) - 1) + [self.total_pop])
        self.min_value = 0

    def __repr__(self):
        return "Population equality"

    def __call__(self, graph):
        """Returns the mean absolute deviation of subgraph population."""        
        components = nx.connected_component_subgraphs(graph)

        goal = self.total_pop / DISTRICTS
        score = 0
        count = 0
        for component in components:
            size = sum([data.get('pop') for _, data in component.nodes(data=True)])
            score += abs(size - goal)
            count += 1
        assert count == DISTRICTS, count
        return -1 * score

class SizeEquality():
    # pylint: disable=R0903
    """Test size equality. For testing purposes only"""
    def __init__(self, graph):
        self.total_pop = len(graph)
        self.max_value = statistics.stdev([0] * (len(graph) - 1) + [self.total_pop])
        self.min_value = 0

    def __repr__(self):
        return "Size equality"

    def __call__(self, graph):
        """Returns the mean absolute deviation of subgraph population."""        
        components = nx.connected_component_subgraphs(graph)

        goal = len(graph) / DISTRICTS # average of n/d nodes per component
        score = 0
        count = 0
        for component in components:
            size = len(component)
            score += abs(size - goal)
            count += 1
        assert count == DISTRICTS, count
        return -1 * score


OBJECTIVES = [PopulationEquality]
