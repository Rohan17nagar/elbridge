"""Various utility classes and methods."""
import os
from collections import defaultdict
import networkx as nx

class cd:
    # pylint: disable=invalid-name, too-few-public-methods
    """Context manager for changing the current working directory."""
    def __init__(self, new_path):
        """Point this to new_path."""
        self.new_path = os.path.expanduser(new_path)
        self.saved_path = None

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)

def chromosome_to_components(graph, vertex_set):
    """Converts a vertex set to components."""
    component_lists = defaultdict(list)
    vertex_list = list(graph.nodes(data=True))

    for idx, comp_idx in enumerate(vertex_set):
        vertex = vertex_list[idx]
        component_lists[comp_idx].append(vertex)
    return component_lists

def get_index(graph, vertex):
    """Take a vertex, find its index in the graph, and return that position in
    the chromosome."""
    assert isinstance(graph, nx.OrderedGraph)
    vertices = list(graph)
    if isinstance(vertex, tuple) and isinstance(vertex[1], dict):
        # remove data from vertex if exists
        vertex, _ = vertex

    index = vertices.index(vertex)
    return index

def get_component(chromosome, graph, vertex):
    """Take a vertex, find its index in the graph, and return that position in
    the chromosome."""
    return chromosome[get_index(graph, vertex)]
