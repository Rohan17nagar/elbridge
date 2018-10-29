"""Genetic algorithm stuff."""

import functools
import random
from multiprocessing.pool import ThreadPool as TPool
from typing import List, Tuple

import networkx as nx
from tqdm import tqdm

from elbridge.evolution.candidate import Candidate
from elbridge.evolution.chromosome import Chromosome
from elbridge.evolution.objectives import ObjectiveFunction

# use this to mute tqdm
# tqdm = lambda x, *y, **z: x

Population = List[Candidate]
Frontier = List[Candidate]


def fast_non_dominated_sort(population: Population) -> List[Frontier]:
    """Take a population P and sort it into fronts F1, F2, ..., Fn."""
    fronts: List[Frontier] = [[]]

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
    for idx, obj_fn in enumerate(Chromosome.objectives):
        # sort by each objective function
        frontier.sort(key=lambda p, index=idx: p.chromosome.get_scores()[index])

        # the boundary points for each objective should always be preserved
        frontier[0].distance = float('inf')
        frontier[-1].distance = float('inf')

        objective_range = obj_fn.max_value - obj_fn.min_value
        for i, elem in enumerate(frontier[1:-1]):
            score_range = abs((frontier[i+1].chromosome.get_scores()[idx] - frontier[i-1].chromosome.get_scores()[idx]))
            elem.distance += score_range / objective_range


def crowding_operator(p: Candidate, q: Candidate) -> int:
    """Return 1 if p << q; -1 otherwise. Used to sort population."""
    if (p.rank < q.rank) or ((p.rank == q.rank) and (p.distance > q.distance)):
        return -1
    elif (p.rank == q.rank) and (p.distance == q.distance):
        return 0
    return 1


def select_parent(population: Population, k: int = 3) -> Candidate:
    return min(random.sample(population, k), key=functools.cmp_to_key(crowding_operator))


def make_children(parents: Population, mutation_probability: float) -> Population:
    """Take a parent population and return an equally-sized child population."""
    children = []  # type: Population
    for _ in range(len(parents) // 2):
        parent_a, parent_b = (select_parent(parents), select_parent(parents))
        offspring = parent_a.crossover_and_mutate(parent_b, mutation_probability)
        children += offspring

    return children


def optimize_children(raw_children: Population, multiprocess: bool = True) -> Population:
    _optimize = lambda idx_child: idx_child[1].optimize(pos=idx_child[0])

    if multiprocess:
        with TPool() as p:
            children = list(tqdm(
                p.imap(_optimize, enumerate(raw_children)), total=len(raw_children), desc="Optimizing children"
            ))
    else:
        children = []
        for idx, child in tqdm(enumerate(raw_children), total=len(raw_children), desc="Optimizing children"):
            children.append(_optimize((idx, child)))

    return children


def evaluate_generation(parents: Population, children: Population) -> Tuple[Population, Frontier]:
    combined_population: Population = parents + children
    frontiers: List[Frontier] = fast_non_dominated_sort(combined_population)

    next_parents: Population = []
    remaining_slots = len(parents)

    for frontier in frontiers:
        crowding_distance_assignment(frontier)
        next_parents += frontier

        remaining_slots -= len(frontier)
        if remaining_slots <= 0:
            break

    next_parents.sort(key=functools.cmp_to_key(crowding_operator))
    return next_parents[:len(parents)], frontiers[0]


@profile
def run_nsga2(master_graph: nx.Graph, objective_fns: List[ObjectiveFunction],
              max_generations: int = 500, pop_size: int = 300, multiprocess: bool = True,
              optimize: bool = True, optimization_interval: int = 20,
              mutation_probability: float = 0.7, mutation_degradation_rate: float = 0.9) -> Tuple[Frontier, dict]:
    """
    Run NSGA-II on a graph.
    """
    Chromosome.objectives = objective_fns

    parents = [Candidate(Chromosome.generate(master_graph)) for _ in range(pop_size)]
    pareto_frontier: Frontier = None
    data_output = {}

    for gen in tqdm(range(1, max_generations + 1), desc="Evolving..."):
        try:
            raw_children = make_children(parents, mutation_probability)

            children = raw_children
            if optimize and gen % optimization_interval == 0:
                children = optimize_children(raw_children, multiprocess=multiprocess)

            parents, pareto_frontier = evaluate_generation(parents, children)

            print("pareto frontier {}/{} (score {})".format(
                len(pareto_frontier), 2 * len(parents), pareto_frontier[0].chromosome.get_scores())
            )

            data_output[gen] = {
                'pareto_frontier': pareto_frontier,
                'unique_parents': len(set(parents))
            }

            mutation_probability *= mutation_degradation_rate
        except KeyboardInterrupt:
            break

    return pareto_frontier, data_output
