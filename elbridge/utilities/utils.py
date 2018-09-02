"""Various utility classes and methods."""
import os
from typing import List

from elbridge.evolution.chromosome import Chromosome
from elbridge.utilities.types import Node, FatNode


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


def _fast_bfs(source, graph, chromosome):
    _seen = set()
    next_level = {source}
    while next_level:
        this_level = next_level
        next_level = set()
        for vertex in this_level:
            if vertex not in _seen:
                yield vertex
                _seen.add(vertex)
                for n in graph[vertex]:
                    if n not in _seen:
                        if chromosome.in_same_component(vertex, n):
                            next_level.add(n)


def _connected_components(vertices: List[FatNode], chromosome: Chromosome):
    """
    Return the number of connected components in a graph. The edges of the graph are defined as E \ hypotheticals.
    :param graph:
    :param vertices:
    :param hypotheticals:
    :return:
    """
    graph = chromosome.get_master_graph()

    seen = set()
    if isinstance(vertices[0], tuple):
        vertices: List[Node] = list(map(lambda i: i[0], vertices))

    for v in vertices:
        if v not in seen:
            c = set(_fast_bfs(v, graph, chromosome))
            yield c
            seen.update(c)


def number_connected_components(vertices: List[FatNode], chromosome: Chromosome) -> int:
    return sum(1 for _ in _connected_components(vertices, chromosome))
