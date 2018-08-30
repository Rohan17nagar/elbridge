from typing import List, Optional

from networkx import connected_component_subgraphs, Graph

from elbridge.evolution.chromosome import Chromosome
from elbridge.evolution.hypotheticals import HypotheticalSet
from elbridge.evolution.objectives import ObjectiveFunction
from elbridge.readers import shape
from elbridge.types import Node
from elbridge.xceptions import ClassNotInitializedException, SameComponentException, IncompleteHypotheticalsException


class SearchState:
    """Encapsulates a state."""
    objectives: List[ObjectiveFunction] = []

    def __init__(self, hypotheticals: HypotheticalSet, chromosome: Chromosome, scores: Optional[List[float]] = None):
        if not SearchState.objectives:
            raise ClassNotInitializedException(SearchState)
        self.hypotheticals = hypotheticals.copy()
        self.chromosome = chromosome.copy()
        if scores:
            self.scores = scores
        else:
            self.evaluate()

    def __hash__(self):
        return self.hypotheticals.__hash__()

    def __eq__(self, other) -> bool:
        return self.hypotheticals == other.hypotheticals

    def __repr__(self) -> str:
        return str(self.hypotheticals) + " (" + str(self._score_format()) + ")"

    def __del__(self):
        del self.hypotheticals
        del self.chromosome

    def _score_format(self) -> str:
        return "; ".join([
            "{}: {}/{}".format(str(SearchState.objectives[idx]), score, SearchState.objectives[idx].goal_value)
            for idx, score in enumerate(self.scores)
        ])

    def connect_vertices(self, i: Node, j: Node) -> None:
        i_cmp = self.chromosome.get_component(i)
        j_cmp = self.chromosome.get_component(j)
        if i_cmp == j_cmp:
            raise SameComponentException(i, j, i_cmp)

        i_cmp, j_cmp = self.chromosome.join_vertices(j, i)

        master_graph = self.chromosome.get_master_graph()

        # for every node connected to j:
        # if the node is in i's component, realize (j, n)
        # if the node is in j's component, remove (j, n)
        for n in master_graph[j]:
            n_cmp = self.chromosome.get_component(n)
            if n_cmp == i_cmp:
                if (j, n) in self.hypotheticals:
                    self.hypotheticals.remove_edge((j, n))
                else:
                    # hypotheticals *must* contain all edges that aren't in the graph
                    raise IncompleteHypotheticalsException((n, j))
            elif master_graph.has_edge(j, n):
                # not in the hypothetical set, so it must be in the graph
                self.hypotheticals.add_edge((j, n))

    def evaluate(self):
        components = self.chromosome.get_components()
        self.scores = [objective(components, self.hypotheticals) for objective in SearchState.objectives]

    def dominated_by(self, other: 'SearchState') -> bool:
        """Returns true if some scores dominate our score."""
        as_good = True
        better = False
        for idx in range(len(self.scores)):
            if self.scores[idx] > other.scores[idx]:
                as_good = False
                break
            elif self.scores[idx] < other.scores[idx]:
                better = True

        return as_good and better

    def gradient(self, other: 'SearchState') -> float:
        """Calculate the gradient between self and other scores."""
        out = 0
        for idx in range(len(self.scores)):
            out += (other.scores[idx] - self.scores[idx])

        return out

    def plot(self):
        """Plot this state."""
        title = "Chromosome ({})".format(self._score_format())
        shapes = []

        for i, component in enumerate(connected_component_subgraphs(self.graph)):
            shapes += [data.get('shape') for _, data in component.nodes(data=True)]

            print("Component {}".format(i))
            print("Total population: {}\n".format(sum([data.get('pop') for _, data in component.nodes(data=True)])))

        shape.plot_shapes(shapes, title=title, random_color=True)
