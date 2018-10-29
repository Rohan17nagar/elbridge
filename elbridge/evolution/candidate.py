"""Encapsulates a candidate solution."""

from random import random
from typing import List, Set

from shapely.ops import cascaded_union

from elbridge.evolution import search
from elbridge.evolution.chromosome import Chromosome
from elbridge.readers.plot import plot_shapes
from elbridge.utilities.utils import cd


class Candidate:
    i = 0

    def __init__(self, chromosome: Chromosome):
        self.chromosome = chromosome

        # set of candidates this candidate dominates
        self.dominated_set: Set[int] = set()
        # number of candidates this candidate is dominated by
        self.domination_count: int = 0
        # this candidate's front
        self.rank: int = 0
        # distance to other candidates on front
        self.distance: int = 0

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
            child.normalize()
            out.append(Candidate(child))

        return out

    def optimize(self, pos=0):
        """Convert a candidate into a state, optimize, and convert back."""
        state = search.optimize(self.chromosome, pos=pos, steps=20, sample_size=50)
        state.normalize()

        return Candidate(state)

    def export(self):
        with cd('out/chromosome_{}/'.format(self.name)):
            with open('elements.csv') as outfile:
                outfile.write(','.join(['element', 'population', 'component']) + '\n')
                graph = self.chromosome.get_master_graph()
                for vertex in graph:
                    data = graph.nodes[vertex]
                    component_idx = self.chromosome.get_component(vertex)
                    outfile.write(','.join([str(vertex), str(data.get('pop', 0)), str(component_idx)]) + '\n')

            with open('components.csv') as outfile:
                component_scores = self.chromosome.get_component_scores()
                outfile.write(','.join(['component'] + Chromosome.__scores__) + "\n")

                for component in component_scores:
                    scores = component_scores[component]
                    outfile.write(','.join([str(component)] + [str(scores[name]) for name in Chromosome.__scores__]))
                    outfile.write('\n')

    def plot(self, save=False):
        """Plots a chromosome."""
        graph = self.chromosome.get_master_graph()

        plot_shapes(
            [
                cascaded_union([data.get('shape') for data in [graph.nodes[node] for node in component]])
                for component in self.chromosome.get_components().values()
            ],
            outdir='out/chromosome_{}/'.format(self.name) if save else '',
            random_color=True,
            title="Candidate {} ({})".format(self.name, self.chromosome.score_format())
        )
