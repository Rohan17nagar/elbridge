"""Various utility classes and methods."""
import os
from collections import defaultdict

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
    for vertex, data in graph.nodes(data=True):
        comp = get_component(vertex_set, graph, vertex)
        component_lists[comp].append((vertex, data))
    return component_lists

def get_index(graph, vertex):
    """Take a vertex, find its index in the graph, and return that position in
    the chromosome."""
    assert "order" in graph.graph
    return graph.graph['order'][vertex]

def get_component(chromosome, graph, vertex):
    """Take a vertex, find its index in the graph, and return that position in
    the chromosome."""
    return chromosome[get_index(graph, vertex)]
