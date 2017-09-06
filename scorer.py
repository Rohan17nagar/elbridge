"""Implements a handful of scoring functions."""
from math import pi

import networkx as nx

WEIGHTS = [0.999, 0.001]

def size_deviation(graph, num_comps):
    """Takes a graph and returns the mean absolute deviation in component size."""
    comps = nx.connected_components(graph)
    goal = float(len(graph)) / num_comps

    total_deviation = 0
    for comp in comps:
        total_deviation += abs(goal - len(comp))

    return (-1 * total_deviation / (2 * goal * (num_comps - 1))) + 1

def polsby_popper(graph):
    """Takes a graph and returns the Polsby-Popper score (area of shape / area of circle with same
        perimeter) for each component."""
    comps = nx.connected_components(graph)
    num_comps = nx.number_connected_components(graph)

    average = 0
    for comp in comps:
        subgraph = graph.subgraph(comp)
        area = sum([graph.node[n]['block'].area for n in comp])
        length = sum([graph.node[n]['block'].length for n in comp])
    
        for (_, _, data) in subgraph.edges(data=True):
            length -= 2 * data['border']
            average += 4 * pi * area / (length ** 2)

    return average / num_comps

def score(state):
    """Return an array of scores."""
    graph = state.G
    k = state.k

    return [size_deviation(graph, k), polsby_popper(graph)]
