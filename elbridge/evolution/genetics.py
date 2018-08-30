# pylint: disable=C0103
"""Genetic algorithm stuff."""

import functools
import random
from multiprocessing.pool import ThreadPool as TPool
from typing import List, Tuple, Any, Dict

import networkx as nx
from tqdm import tqdm

from elbridge.evolution.candidate import Candidate
from elbridge.evolution.objectives import ObjectiveFunction
from elbridge.evolution.search import SearchState

# use this to mute tqdm
tqdm = lambda x, *y, **z: x

Population = List[Candidate]
Frontier = List[Candidate]
Parents = Tuple[Candidate, Candidate]


def fast_non_dominated_sort(population: Population) -> List[Frontier]:
    """Take a population P and sort it into fronts F1, F2, ..., Fn."""
    fronts: List[List[Candidate]] = [[]]

    for p in population:
        p.refresh()

    for p in population:
        for i, q in enumerate(population):
            if p == q:
                continue

            if p.dominates(q):
                p.dominated_set.add(i)
            elif q.dominates(p):
                p.domination_count += 1

        if p.domination_count == 0:
            p.rank = 1
            fronts[0].append(p)

    i = 0
    while fronts[i]:
        next_front = []
        for p in fronts[i]:
            for idx in p.dominated_set:
                q = population[idx]
                q.domination_count -= 1
                if q.domination_count == 0:
                    q.rank = i + 1
                    next_front.append(q)

        i += 1
        fronts.append(next_front)

    # return everything but the last element, which is always empty
    return fronts[:-1]


def crowding_distance_assignment(frontier: Frontier):
    """Take a Pareto frontier and calculate distances between candidates."""
    for idx, _ in enumerate(Candidate.objectives):
        # sort by each objective function
        frontier.sort(key=lambda p, idx=idx: p.scores[idx])

        # the boundary points for each objective should always be preserved
        frontier[0].distance = float('inf')
        frontier[-1].distance = float('inf')

        for i, _ in enumerate(frontier[1:-1]):
            score_range = abs((frontier[i + 1].scores[idx] - frontier[i - 1].scores[idx]))
            objective_range = Candidate.objectives[idx].max_value - Candidate.objectives[idx].min_value
            frontier[i].distance += score_range / objective_range


def crowding_operator(p: Candidate, q: Candidate) -> int:
    """Return 1 if p << q; -1 otherwise. Used to sort population."""
    if (p.rank < q.rank) or ((p.rank == q.rank) and (p.distance > q.distance)):
        return -1
    elif (p.rank == q.rank) and (p.distance == q.distance):
        return 0
    return 1


def select_parent(population: Population, k: int = 3) -> Candidate:
    return sorted(random.sample(population, k), key=functools.cmp_to_key(crowding_operator))[0]


def select_parents(population: Population) -> Parents:
    """Return two parent solutions.

    Uses k-ary tournament selection, where k individuals are selected and ranked by the
    crowding comparison operator.

    If random_select is True, randomly choose parents."""
    parents = (select_parent(population), select_parent(population))

    return parents


def make_children(parents: Population) -> Population:
    """Take a parent population and return an equally-sized child population."""
    children = []
    for _ in tqdm(range(len(parents) // 2), desc="Making children"):
        parent_a, parent_b = select_parents(parents)
        offspring = parent_a.crossover_and_mutate(parent_b)
        children += offspring

    return children


def make_adam_and_eve(master_graph: nx.Graph, population_size: int) -> Population:
    """Makes the first generation."""
    parents = [Candidate.generate(master_graph) for _ in tqdm(range(population_size), desc="Creating first parents")]
    return parents


def _optimize(arg):
    pos, c = arg
    return c.optimize(pos)


def _optimize_children(raw_offspring: Population, multiprocess=True) -> Population:
    offspring = []
    if multiprocess:
        with TPool() as p:
            for child in tqdm(p.imap_unordered(_optimize, enumerate(raw_offspring)), total=len(raw_offspring),
                              desc="Optimizing children"):
                offspring.append(child)
    else:
        for idx_child in tqdm(enumerate(raw_offspring), desc="Optimizing children"):
            offspring.append(_optimize(idx_child))

    return offspring


def _get_best_frontier(frontiers: List[Frontier]):
    return set([tuple(cand.scores) for cand in frontiers[0]])


def evaluate_generation(parents, offspring):
    combined_population = parents + offspring
    frontiers = fast_non_dominated_sort(combined_population)

    next_parents: Population = []
    remaining_slots = len(parents)
    i = 0

    while i < len(frontiers):
        frontier = frontiers[i]

        crowding_distance_assignment(frontier)
        next_parents += frontier

        remaining_slots -= len(frontier)
        if remaining_slots <= 0:
            break
        i += 1

    next_parents.sort(key=functools.cmp_to_key(crowding_operator))

    return next_parents[:len(parents)], frontiers


@profile
def run_nsga2(master_graph: nx.Graph, config: Dict[str, Any],
              objective_fns: List[Tuple[ObjectiveFunction, Dict[str, Any]]]):
    # pylint: disable=dangerous-default-value, too-many-locals, too-many-branches, too-many-statements
    """Runs NSGA-II."""
    Candidate.objectives = SearchState.objectives = [cls(master_graph, **args) for cls, args in objective_fns]

    # how many generations to run for
    max_generations: int = config.get("generations", 500)

    # how many candidates to evaluate
    pop_size: int = config.get("population_size", 300)

    # whether to run in parallel
    multiprocess: bool = config.get("multiprocess", True)

    # whether to optimize
    optimize: bool = config.get("optimize", True)

    # how frequently (# of generations) candidates should be optimized
    optimization_interval: int = config.get("optimization_interval", 20)

    _data_output = {
        'pareto_per_gen': [],           # best frontier in each generation
        'final_gen': max_generations,   # last evaluated generation
    }

    Candidate.mutation_probability = config.get('mutation_probability', 0.7)

    print("Starting NSGA-II. Running for {} generations with a population of {}.".format(max_generations, pop_size))
    parents = make_adam_and_eve(master_graph, pop_size)
    frontiers = []

    for gen in tqdm(range(1, max_generations + 1), desc="Evolving..."):
        try:
            raw_offspring = make_children(parents)
            if optimize and ((gen + 1) % optimization_interval == 0):
                offspring = _optimize_children(raw_offspring, multiprocess=multiprocess)
            else:
                offspring = raw_offspring

            new_parents, frontiers = evaluate_generation(parents, offspring)

            _data_output['pareto_per_gen'] += frontiers[0]
            if len(set(new_parents)) == 1:
                _data_output['final_gen'] = gen
                if config.get('early_break', False):
                    break

            parents = new_parents
            Candidate.mutation_probability *= 0.99

        except KeyboardInterrupt:
            print("Interrupted; quitting after {} generations.".format(gen))
            _data_output['final_gen'] = gen
            break

    print("Finished running NSGA-II. Best frontier:", _get_best_frontier(frontiers))
    return frontiers[0], _data_output
