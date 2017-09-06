"""DEAP (Distributed Evolutionary Algorithms in Python) testing."""
from collections import defaultdict

import networkx as nx

def _size_deviation(subgraph, desired_mean):
    return abs(len(subgraph) - desired_mean)

def _wasted_votes(subgraph):
    wasted_votes = 0
    for vertex in subgraph:
        if vertex['DEM'] > vertex['REP']:
            dem_wasted_votes = vertex['DEM'] - (vertex['REP'] + 1)
            rep_wasted_votes = vertex['REP']
        else:
            rep_wasted_votes = vertex['REP'] - (vertex['DEM'] + 1)
            dem_wasted_votes = vertex['DEM']

        wasted_votes += dem_wasted_votes - rep_wasted_votes

    return wasted_votes



def evaluate_sample(individual, G, k):
    """Takes an individual string and returns the fitness.

    Keyword arguments:
    -- individual: the individual in the genetic search space (a list of numbers)
    -- G: the graph
    """

    # the individual is an array, where individual[i] = j means that vertex i is in component j
    components = defaultdict(list)
    for idx, val in enumerate(individual):
        components[val].append(idx)

    mean_absolute_deviation = 0
    desired_mean = len(G) / k # the number of vertices per connected component
    wasted_votes = 0

    for component in components:
        subgraph = G.subgraph(component)
        if not nx.is_connected(G):
            return float('-inf') # this is an illegal state

        mean_absolute_deviation += _size_deviation(subgraph, desired_mean)
        wasted_votes += _wasted_votes(subgraph)

    return (mean_absolute_deviation, wasted_votes)
