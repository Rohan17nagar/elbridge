from typing import List, Optional

from networkx import connected_component_subgraphs

from elbridge.evolution.chromosome import Chromosome
from elbridge.evolution.objectives import ObjectiveFunction
from elbridge.readers import shape
from elbridge.utilities.types import Node
from elbridge.utilities.xceptions import ClassNotInitializedException


class SearchState:
    """Encapsulates a state."""
    objectives: List[ObjectiveFunction] = []

    def __init__(self, chromosome: Chromosome, scores: Optional[List[float]] = None):
        if not SearchState.objectives:
            raise ClassNotInitializedException(SearchState)

        self.chromosome = chromosome.copy()
        self.scores = scores or []

    def __hash__(self):
        return self.chromosome.__hash__()

    def __eq__(self, other) -> bool:
        return self.chromosome == other.chromosome

    def __repr__(self) -> str:
        return str(self.chromosome) + " (" + str(self._score_format()) + ")"

    def __del__(self):
        del self.chromosome

    def _score_format(self) -> str:
        return "; ".join([
            "{}: {}/{}".format(str(SearchState.objectives[idx]), score, SearchState.objectives[idx].goal_value)
            for idx, score in enumerate(self.scores)
        ])

    def connect_vertices(self, i: Node, j: Node) -> None:
        self.chromosome.join_vertices(j, i)

    def evaluate(self):
        self.scores = [objective(self.chromosome) for objective in SearchState.objectives]

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
