"""Objective functions. These functions take a chromosome and return a value, such that better 
chromosomes have higher values."""

import statistics
import networkx as nx

DISTRICTS = 10

class PopulationEquality():
    # pylint: disable=R0903
    """Test population equality."""
    def __init__(self, graph, key='pop'):
        self.key = key

        self.total_pop = sum([data.get(self.key, 0) for _, data in
                              graph.nodes(data=True)])
        # self.min_value = -1 * statistics.stdev([0] * (len(graph) - 1) +
                                               # [self.total_pop])
        # self.max_value = 0
        self.min_value = 0
        self.max_value = self.total_pop / DISTRICTS

    def __repr__(self):
        return "Population equality"

    @profile
    def __call__(self, components, graph, with_data=False):
        """Returns the mean absolute deviation of subgraph population."""
        # score = -1 * sum([abs(sum([data.get(self.key) for _, data in component]) -
                              # goal) for component in components])
        # goal = self.total_pop / DISTRICTS
        score = float('inf')
        data = {}
        for component in components:
            component_score = 0
            for _, data in component:
                if self.key not in data:
                    print(components)
                    print(graph.nodes(data=True))
                    assert False
                
                component_score += data.get(self.key)
            
            score = min(score, component_score)
            # score += abs(component_score - goal)

        # punish district maps with more or less than d ccomps
        # this punishes disconnected districts
        ncc = nx.number_connected_components(graph)
        score -= 100 * abs(ncc - DISTRICTS)
        data['components'] = ncc

        # punish district maps with more or less than d districts
        score -= 1000 * abs(len(components) - DISTRICTS)
        data['districts'] = len(components)

        if with_data:
            return score, data

        return score


class SizeEquality():
    # pylint: disable=R0903
    """Test size equality. For testing purposes only"""
    def __init__(self, graph):
        self.total_pop = len(graph)
        self.min_value = -1 * statistics.stdev([0] * (len(graph) - 1) +
                                               [self.total_pop])
        self.max_value = 0
        # self.min_value = 0
        # self.max_value = self.total_pop / DISTRICTS

    def __repr__(self):
        return "Size equality"

    def __call__(self, components, graph):
        """Returns the mean absolute deviation of subgraph population."""
        goal = self.total_pop / DISTRICTS
        score = -1 * sum([abs(len(component) - goal) for component in components])
        # punish district maps with more or less than d ccomps
        # this punishes disconnected districts
        ncc = nx.number_connected_components(graph)
        score -= 100 * abs(ncc - DISTRICTS)

        # punish district maps with more or less than d districts
        score -= 1000 * abs(len(components) - DISTRICTS)
        return score
