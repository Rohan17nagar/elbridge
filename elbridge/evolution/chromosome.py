from collections import defaultdict
from random import randint, randrange
from typing import List, Tuple

from networkx import Graph, is_frozen

from elbridge.evolution.hypotheticals import HypotheticalSet
from elbridge.types import Node


class Chromosome:
    """
    Chromosome. Stores an (immutable) master graph
    """
    def __init__(self, graph: Graph, vertex_set: List[Node]):
        if not is_frozen(graph):
            raise Exception("Master graph must be frozen")

        self._graph = graph
        if 'order' not in graph.graph:
            # require an order on the graph for consistency
            # order[i] = j implies that vertex i is located at index j in vertex_set
            self._graph.graph['order'] = {vertex: idx for idx, vertex in enumerate(self._graph)}

        self._assignment = vertex_set[:]
        self._normalize()

    def copy(self):
        return Chromosome(self._graph, self._assignment[:])

    def __eq__(self, other):
        return self._assignment == other._assignment

    def __hash__(self):
        return tuple(self._assignment).__hash__()

    def _normalize(self):
        # normalize the chromosome: [1, 2, 3, 5, 4] -> [1, 2, 3, 4, 5]
        mapping = {}
        ind = 1
        normalized_assignment = []
        for idx in range(len(self._assignment)):
            cur_comp = self._assignment[idx]
            if cur_comp not in mapping:
                mapping[cur_comp] = ind
                ind += 1
            normalized_assignment.append(mapping.get(cur_comp))

        self._assignment = normalized_assignment

    def get_master_graph(self):
        return self._graph

    def get_assignment(self):
        return self._assignment

    def join_vertices(self, j: Node, i: Node):
        """
        Sets j's component to i, and returns the new components of both.

        NOTE: this function calls _normalize, which is correct behavior (the chromosome should always be normalized).
        However, this could change component assignments, so any calls to get_component should be assumed to be wrong.
        :param j:
        :param i:
        :return: None.
        """
        j_index = self.get_index(j)
        i_cmp = self.get_component(i)

        self._assignment[j_index] = i_cmp
        self._normalize()

        return self.get_component(i), self.get_component(j)

    def get_hypotheticals(self) -> HypotheticalSet:
        """
        Get the graph corresponding to this chromosome.
        :return:
        """
        hypotheticals = HypotheticalSet(set())

        for i, j in self._graph.edges():
            if self.get_component(i) != self.get_component(j):
                # vertices i and j are in different components; remove the edge
                hypotheticals.add_edge((i, j))

        return hypotheticals

    def crossover(self, other: 'Chromosome') -> List['Chromosome']:
        split_point = randrange(len(self._assignment))

        chromosome_a = self._assignment[:split_point] + other._assignment[split_point:]
        chromosome_b = other._assignment[:split_point] + self._assignment[split_point:]

        return [Chromosome(self._graph, chromosome_a), Chromosome(self._graph, chromosome_b)]

    def mutate(self):
        element = randrange(len(self._assignment))
        self._assignment[element] = randint(1, max(self._assignment))

    def get_index(self, vertex: Node) -> int:
        """
        Get the index of a given vertex into the vertex set.
        :param vertex:
        :return:
        """
        return self._graph.graph['order'][vertex]

    def get_component(self, vertex: Node) -> int:
        """
        Get the component of a given vertex.
        :param vertex:
        :return:
        """
        vertex_index = self.get_index(vertex)
        return self._assignment[vertex_index]

    def get_components(self) -> List[list]:
        """
        Return a map of component IDs to vertices in that component.
        :return:
        """
        components = defaultdict(list)
        for vertex, data in self._graph.nodes(data=True):
            vertex_component = self.get_component(vertex)
            components[vertex_component].append((vertex, data))

        return list(components.values())
