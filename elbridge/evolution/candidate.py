# pylint: disable=C0103
"""Encapsulates a candidate solution."""

from random import random, randint
from typing import List

from shapely.ops import cascaded_union

from elbridge.evolution import objectives, search
from elbridge.evolution.chromosome import Chromosome
from elbridge.evolution.objectives import ObjectiveFunction
from elbridge.readers.plot import plot_shapes
from elbridge.utilities.xceptions import ClassNotInitializedException, InconsistentSearchStateException


class Candidate:
    # pylint: disable=R0902
    """
    Encapsulates a candidate solution.

    The chromosome is given by an |E|-length real array A, where A[i] is the order in which edge i
    is added to the graph.

    The Candidate class *must* be "initialized" first by assigning a global
    master graph and a global mutation probability.
    """
    i = 0
    mutation_probability = 0
    objectives: List[ObjectiveFunction] = []

    @profile
    def __init__(self, chromosome: Chromosome):
        if not Candidate.objectives:
            raise ClassNotInitializedException(Candidate)
        # |V|-length array where vs[i] = j means that vertex i is in district j
        self.chromosome = chromosome

        # set of candidates this candidate dominates
        self.dominated_set = set()
        # number of candidates this candidate is dominated by
        self.domination_count = 0
        # this candidate's front
        self.rank = 0
        # distance to other candidates on front
        self.distance = 0

        self.scores_and_data = [
            objective.call_with_data(self.chromosome) for objective in Candidate.objectives
        ]
        self.scores = [score[0] for score in self.scores_and_data]
        self.score_data = [score[1] for score in self.scores_and_data]

        self.name = Candidate.i
        Candidate.i += 1

    def _score_format(self):
        return "; ".join(["{}: {}/{}".format(
            str(Candidate.objectives[idx]), self.scores[idx], Candidate.objectives[idx].goal_value
        ) for idx in range(len(Candidate.objectives))])

    def __repr__(self):
        return str(self.name) + " (" + self._score_format() + ")"

    def __eq__(self, other):
        return self.chromosome == other.chromosome

    def __hash__(self):
        return self.chromosome.__hash__()

    def refresh(self):
        """Clear out NSGA stuff."""
        self.dominated_set = set()
        self.domination_count = 0
        self.rank = 0
        self.distance = 0

    @staticmethod
    def generate(graph) -> 'Candidate':
        """Create a new random candidate."""
        assignment = Chromosome(graph, [randint(1, objectives.DISTRICTS) for _ in range(len(graph))])
        return Candidate(assignment)

    def dominates(self, other: 'Candidate') -> bool:
        """
        Returns True if p dominates q.

        Domination is defined as a partial ordering < on solutions, where
        for some objectives f1, f2, ..., fm, p < q iff for all i <= m fi(p) >= fi(q).
        """
        as_good = True
        better = False
        for i in range(len(self.scores)):
            if self.scores[i] < other.scores[i]:
                as_good = False
                break
            if self.scores[i] > other.scores[i]:
                better = True

        return as_good and better

    def crossover_and_mutate(self, other: 'Candidate') -> List['Candidate']:
        new_candidates = self.chromosome.crossover(other.chromosome)

        out = []
        for child in new_candidates:
            if random() < Candidate.mutation_probability:
                child.mutate()
            out.append(Candidate(child))

        return out

    def optimize(self, pos=0):
        """Convert a candidate into a state, optimize, and convert back."""
        state = search.optimize(self.chromosome, pos=pos, steps=20, sample_size=50)
        out = Candidate(state.chromosome)

        if not out.scores == state.scores:
            raise InconsistentSearchStateException(state, out)

        return out

    def plot(self, save=False):
        """Plots a chromosome."""
        title = "Candidate {} ({})".format(self.name, self._score_format())

        output = title + "\n"
        shapes = []

        for idx, component in self.chromosome.get_components():
            comp_shape = cascaded_union([data.get('shape') for _, data in component])
            shapes.append(comp_shape)

            output += "Component {}:\n\t".format(i)
            output += "Total population: {}\n".format(sum([d.get('pop') for _, d in component]))
            output += "Elements:\n\t"
            output += "\n\t".join(["Unit {} (pop {})".format(n, data.get('pop')) for n, data in component])
            output += "\n\n"

        if save:
            with open('out/' + title + '.txt', 'w+') as outfile:
                outfile.write(output)
        else:
            print(output)

        plot_shapes(shapes, random_color=True, title=title, save=save)
