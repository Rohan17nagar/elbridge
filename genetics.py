# pylint: disable=C0103
"""Genetic algorithm stuff."""

import random
import functools
from multiprocessing import Pool
from datetime import datetime

from objectives import OBJECTIVES as objective_funcs
from candidate import Candidate

import networkx as nx
from tqdm import tqdm

POOL = None

# use this to mute tqdm
# tqdm = lambda x, *y: x

# @profile
def _assign_rank(population, elem):
    p = elem.copy()
    for i, q in enumerate(population):
        if p == q:
            continue

        if p.dominates(q):
            p.dominated_set.add(i)
        elif q.dominates(p):
            p.domination_count += 1

    if p.domination_count == 0:
        p.rank = 1

    return p

def fast_non_dominated_sort(population):
    """Take a population P and sort it into fronts F1, F2, ..., Fn."""
    fronts = [[]]

    n_population = list(map(functools.partial(_assign_rank, population),
                            population))

    fronts[0] = [p for p in n_population if p.rank == 1]

    i = 0
    # pylint: disable=C1801
    while len(fronts[i]) != 0:
        next_front = []
        for p in fronts[i]:
            for idx in p.dominated_set:
                q = n_population[idx]
                q.domination_count -= 1
                if q.domination_count == 0:
                    q.rank = i + 1
                    next_front.append(q)

        i += 1
        fronts.append(next_front)

    # print("\n".join(map(str, fronts)))

    # print([(len(front), front[0]) for front in fronts[:-1]])
    return fronts[:-1]

def crowding_distance_assignment(frontier):
    """Take a Pareto frontier and calculate distances between candidates."""
    for idx, _ in enumerate(Candidate.objectives):
        frontier.sort(key=lambda p, idx=idx: p.scores[idx])

        # the boundary points for each objective should always be preserved
        frontier[0].distance = float('inf')
        frontier[-1].distance = float('inf')

        for i, _ in enumerate(frontier[1:-1]):
            frontier[i].distance += abs((frontier[i+1].scores[idx] \
                - frontier[i-1].scores[idx])) \
                / (Candidate.objectives[idx].max_value - Candidate.objectives[idx].min_value)

def crowding_operator(p, q):
    """Return 1 if p << q; -1 otherwise. Used to sort last frontier."""
    if (p.rank < q.rank) or ((p.rank == q.rank) and (p.distance > q.distance)):
        return -1
    elif (p.rank == q.rank) and (p.distance == q.distance):
        return 0
    return 1

def make_adam_and_eve(graph, population_size):
    """Makes the first generation."""
    num_edges = len(graph.edges())
    parents = [[random.random() for i in range(num_edges)] for _ in range(population_size)]

    parents = list(map(Candidate, parents))

    offspring = list(map(_make_children, [random.sample(parents, 2)
                                          for i in range(len(parents) // 2)]))
    offspring = [child for pair in offspring for child in pair]
    return parents, offspring

def select_parents(population):
    """Return two parent solutions.

    Uses binary tournament selection, where two individuals are selected and ranked by the
    crowding comparison operator."""
    parents = [None, None]
    while parents[0] == parents[1]:
        parents = [random.choice(population), random.choice(population)]
    # for i in range(2):
        # pick two elements of the population
        # choices = random.sample(population, 3)
        # parents[i] = sorted(choices,
                             # key=functools.cmp_to_key(crowding_operator))[0]

    return parents

def _make_children(parents):
    [parent_a, parent_b] = parents
    offspring = parent_a.crossover(parent_b)
    for child in offspring:
        child.mutate()

    return offspring

def make_children(parents):
    """Take a parent population and return an equally-sized child population."""
    children = map(_make_children, [select_parents(parents) for i in
                                    range(len(parents) // 2)])
    return [child for sublist in children for child in sublist]

@profile
def evolve(graph, max_generations=500, pop_size=300, mutation_probability=0.7):
    # pylint: disable=R0915, W0603, R0914
    """Runs NSGA-II."""
    Candidate.master_graph = graph

    Candidate.objectives = [obj(graph) for obj in objective_funcs]

    Candidate.mutation_probability = mutation_probability

    global POOL
    POOL = Pool(4)

    print("Starting NSGA-II. Running for {gens} generations with a population of {pop}."
          .format(gens=max_generations, pop=pop_size))

    print("Building initial population...")
    parents, offspring = make_adam_and_eve(graph, pop_size)

    best_scores = []

    for gen in tqdm(range(1, max_generations), "Evolving..."):
        try:
            combined_population = parents + offspring
            frontiers = fast_non_dominated_sort(combined_population)

            print("Best element in generation", str(gen) + ":", str(frontiers[0][0]))
            best_scores.append(frontiers[0][0].scores)

            next_parents = []
            remaining_slots = len(parents)
            i = 0

            while i < len(frontiers):
                frontier = frontiers[i]
                if remaining_slots < len(frontier):
                    # continue until you can't add any more
                    break

                crowding_distance_assignment(frontier)
                next_parents += frontier

                remaining_slots -= len(frontier)
                i += 1

            print("Used", i, "of", len(frontiers), "frontiers.", remaining_slots, "slots remaining.")
            if remaining_slots != 0:
                # fill the remaining slots with the best elements of frontier[i]
                # this sorts x = (r1, d1) and y = (r2, d2) as x < y
                # if r1 < r2 or r1 == r2 and d1 > d2
                frontiers[i].sort(key=functools.cmp_to_key(crowding_operator))
                next_parents += frontiers[i][:remaining_slots]

            parents = next_parents

            offspring = make_children(parents)
            Candidate.mutation_probability *= 0.99
        except KeyboardInterrupt:
            # stops at current generation
            break

    POOL.close()
    POOL.join()

    print()
    print("Finished running NSGA-II. Best candidate:", frontiers[0][0])

    # frontiers[0][0].plot(save=True)

    return frontiers[0]

def test():
    """Testing function."""
    import matplotlib.pyplot as plt
    graph = nx.Graph()
    N = 50
    for i in range(N):
        graph.add_node(i, pop=i+1)
    for i in range(N):
        for j in range(i, N):
            graph.add_edge(i, j)
    final = evolve(graph)[0]
    new_graph = final.reconstruct_graph()
    nx.draw_networkx(new_graph)
    plt.show()

if __name__ == "__main__":
    test()
