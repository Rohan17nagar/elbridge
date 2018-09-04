from collections import defaultdict
from random import randint, randrange
from typing import List, Dict, Optional, DefaultDict, TYPE_CHECKING

import matplotlib.pyplot as plt
from networkx import Graph, is_frozen, freeze, nx, connected_component_subgraphs

from elbridge.evolution.hypotheticals import HypotheticalSet
from elbridge.readers.plot import plot_shapes
from elbridge.utilities.types import Node, Component, FatNode, Edge
from elbridge.utilities.utils import dominates, gradient, number_connected_components
from elbridge.utilities.xceptions import SameComponentException, ClassNotInitializedException

if TYPE_CHECKING:
    from elbridge.evolution.objectives import ObjectiveFunction


class Chromosome:
    """
    Chromosome. Stores an (immutable) master graph.
    """
    objectives = []  # type: List[ObjectiveFunction]

    @profile
    def __init__(self, graph: Graph, assignment: List[int], components: Optional[DefaultDict[int, Component]] = None,
                 component_scores: Optional[Dict[int, Dict[str, float]]] = None):
        if not Chromosome.objectives:
            raise ClassNotInitializedException(Chromosome)

        if not is_frozen(graph):
            self._graph = freeze(graph)
        else:
            self._graph = graph

        if 'order' not in graph.graph:
            # require an order on the graph for consistency
            # order[i] = j implies that vertex i is located at index j in vertex_set
            self._graph.graph['order'] = {vertex: idx for idx, vertex in enumerate(self._graph)}

        self._assignment: List[int] = assignment
        self._components: Dict[int, Component] = defaultdict(set)
        self._component_scores: Dict[int, Dict[str, float]] = {}
        self._scores: List[float] = None

        if components:
            self._components = components
        else:
            self._rebuild_components()

        if component_scores:
            self._component_scores = component_scores
        else:
            self._compute_component_scores()

        self._compute_scores()

    def _rebuild_components(self) -> None:
        """
        Return a map of component IDs to vertices in that component.
        :return:
        """
        components = defaultdict(set)
        for vertex in self._graph.nodes():
            vertex_component = self.get_component(vertex)
            components[vertex_component].add(vertex)

        self._components = components

    def _compute_component_scores(self):
        components = self._components.items()

        # for each component, compute all necessary scores
        for idx, _component in components:
            component_graph = nx.subgraph(self._graph, _component)
            component_score = {
                'total_pop': sum(self._graph.nodes[node]['pop'] for node in _component),
                'components': nx.number_connected_components(component_graph),
            }

            self._component_scores[idx] = component_score

    def _compute_scores(self):
        self._scores = [fn(self) for fn in Chromosome.objectives]

    def copy(self) -> 'Chromosome':
        return Chromosome(self._graph, self._assignment[:])

    def __eq__(self, other):
        return self.get_assignment() == other.get_assignment()

    def __hash__(self):
        return tuple(self._assignment).__hash__()

    def __repr__(self):
        return repr(self._assignment)

    def _score_format(self) -> str:
        return "; ".join([
            "{}: {}/{}".format(str(Chromosome.objectives[idx]), score, Chromosome.objectives[idx].goal_value)
            for idx, score in enumerate(self._scores)
        ])

    def plot_shapes(self):
        """Plot this state."""
        shapes = []

        for i, component in enumerate(connected_component_subgraphs(self._graph)):
            shapes += [data.get('shape') for _, data in component.nodes(data=True)]

            print("Component {}".format(i))
            print("Total population: {}\n".format(sum([data.get('pop') for _, data in component.nodes(data=True)])))

        plot_shapes(shapes, title=self._score_format(), random_color=True)

    def plot_graph(self):
        graph = nx.Graph(self._graph)

        for i, j in self._graph.edges():
            if not self.in_same_component(i, j):
                graph.remove_edge(i, j)

        nx.draw_networkx(graph, pos={v: v for v in graph}, labels={v: "{} {}".format(v, self.get_component(v)) for v in graph})
        plt.title(self._score_format())
        plt.show()

    @profile
    def normalize(self) -> None:
        # normalize the chromosome: [1, 2, 3, 5, 4] -> [1, 2, 3, 4, 5]
        mapping = {}  # old component -> normalized component
        ind = 1

        normalized_assignment = []
        normalized_components: Dict[int, Component] = defaultdict(set)
        normalized_component_scores: Dict[int, Dict[str, float]] = {}

        for current_component in self._assignment:
            if current_component not in mapping:
                mapping[current_component] = ind
                ind += 1

        if all(cur_val == new_val for cur_val, new_val in mapping.items()):
            return

        for current_component in self._assignment:
            normalized_component = mapping[current_component]
            normalized_assignment.append(normalized_component)
            normalized_components[normalized_component] = self._components[current_component]
            normalized_component_scores[normalized_component] = self._component_scores[current_component]

        self._assignment = normalized_assignment
        self._components = normalized_components
        self._component_scores = normalized_component_scores

    def get_master_graph(self) -> Graph:
        return self._graph

    def get_assignment(self) -> List[int]:
        return self._assignment

    def get_index(self, vertex: FatNode) -> int:
        """
        Get the index of a given vertex into the vertex set.
        :param vertex:
        :return:
        """
        return self._graph.graph['order'][vertex]

    def get_component(self, vertex: FatNode) -> int:
        """
        Get the component of a given vertex.
        :param vertex:
        :return:
        """
        vertex_index = self.get_index(vertex)
        return self._assignment[vertex_index]

    def in_same_component(self, i: FatNode, j: FatNode) -> bool:
        return self.get_component(i) == self.get_component(j)

    def get_components(self) -> Dict[int, Component]:
        return self._components

    def get_component_scores(self) -> Dict[int, Dict[str, float]]:
        return self._component_scores

    def get_scores(self) -> List[float]:
        return self._scores

    def get_num_components(self) -> int:
        return len(set(self._assignment))

    def dominates(self, other: 'Chromosome'):
        """Returns true if we dominate another chromosome."""
        return dominates(self._scores, other._scores)

    def gradient(self, other: 'Chromosome') -> float:
        """Calculate the gradient between self and other scores."""
        return gradient(other._scores, self._scores)

    @profile
    def connect_vertices(self, edge: Edge) -> 'Chromosome':
        """
        Moves j to i's component, and returns a new Chromosome.
        """
        i, j = edge
        if self.in_same_component(i, j):
            raise SameComponentException(i, j, self.get_component(i))

        j_index = self.get_index(j)
        i_cmp = self.get_component(i)
        j_cmp = self.get_component(j)

        new_assignment = self._assignment[:]
        new_assignment[j_index] = i_cmp

        components = {c: set(self._components[c]) for c in self._components}
        components[j_cmp].remove(j)
        components[i_cmp].add(j)

        component_scores = {c: {score: value for score, value in d.items()} for c, d in self._component_scores.items()}
        component_scores[j_cmp]['total_pop'] -= self._graph.nodes[j].get('pop')
        component_scores[i_cmp]['total_pop'] += self._graph.nodes[j].get('pop')
        if components[j_cmp]:
            component_scores[j_cmp]['components'] = number_connected_components(self._graph, components[j_cmp])
        else:
            components.pop(j_cmp)
            component_scores.pop(j_cmp)

        return Chromosome(self._graph, new_assignment, components=components, component_scores=component_scores)

    def get_hypotheticals(self) -> HypotheticalSet:
        """
        Get the graph corresponding to this chromosome.
        :return:
        """
        hypotheticals = HypotheticalSet(set())

        for i, j in self._graph.edges():
            if not self.in_same_component(i, j):
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
        self._rebuild_components()
