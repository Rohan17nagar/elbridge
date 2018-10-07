"""Encapsulates a candidate solution."""

from random import random
from typing import List

from shapely.ops import cascaded_union

from elbridge.evolution import search
from elbridge.evolution.chromosome import Chromosome
from elbridge.readers.plot import plot_shapes


class Candidate:
    """
    Encapsulates a candidate solution.

    The chromosome is given by an |E|-length real array A, where A[i] is the order in which edge i
    is added to the graph.

    The Candidate class *must* be "initialized" first by assigning a global
    master graph and a global mutation probability.
    """
    i = 0

    @profile
    def __init__(self, chromosome: Chromosome):
        self.chromosome = chromosome

        # set of candidates this candidate dominates
        self.dominated_set = set()
        # number of candidates this candidate is dominated by
        self.domination_count = 0
        # this candidate's front
        self.rank = 0
        # distance to other candidates on front
        self.distance = 0

        self.name = Candidate.i
        Candidate.i += 1

    def __repr__(self):
        return "{} ({})".format(self.name, self.chromosome.score_format())

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

    def dominates(self, other: 'Candidate') -> bool:
        return self.chromosome.dominates(other.chromosome)

    def crossover_and_mutate(self, other: 'Candidate', mutation_probability: float) -> List['Candidate']:
        new_candidates = self.chromosome.crossover(other.chromosome)

        out = []
        for child in new_candidates:
            if random() < mutation_probability:
                child.mutate()
            out.append(Candidate(child))

        return out

    def optimize(self, pos=0):
        """Convert a candidate into a state, optimize, and convert back."""
        state = search.optimize(self.chromosome, pos=pos, steps=20, sample_size=50)
        state.normalize()

        return Candidate(state)

    def plot(self, save=False):
        """Plots a chromosome."""
        title = "Candidate {} ({})".format(self.name, self.chromosome.score_format())

        output = title + "\n"
        shapes = []

        for idx, component in self.chromosome.get_components():
            comp_shape = cascaded_union([data.get('shape') for _, data in component])
            shapes.append(comp_shape)

            output += "Component {}:\n\t".format(idx)
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
