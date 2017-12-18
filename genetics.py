# pylint: disable=C0103
"""Genetic algorithm stuff."""

import random
import functools
from multiprocessing import Pool
import signal

import objectives
from candidate import Candidate
from search import State

import networkx as nx
from tqdm import tqdm

# use this to mute tqdm
# tqdm = lambda x, *y: x

def fast_non_dominated_sort(population):
    """Take a population P and sort it into fronts F1, F2, ..., Fn."""
    fronts = [[]]

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
    while fronts[i] != []:
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

def crowding_distance_assignment(frontier):
    """Take a Pareto frontier and calculate distances between candidates."""
    for idx, _ in enumerate(Candidate.objectives):
        # sort by each objective function
        frontier.sort(key=lambda p, idx=idx: p.scores[idx])

        # the boundary points for each objective should always be preserved
        frontier[0].distance = float('inf')
        frontier[-1].distance = float('inf')

        for i, _ in enumerate(frontier[1:-1]):
            frontier[i].distance += abs((frontier[i+1].scores[idx] \
                - frontier[i-1].scores[idx])) \
                / (Candidate.objectives[idx].max_value - Candidate.objectives[idx].min_value)

def crowding_operator(p, q):
    """Return 1 if p << q; -1 otherwise. Used to sort population."""
    if (p.rank < q.rank) or ((p.rank == q.rank) and (p.distance > q.distance)):
        return -1
    elif (p.rank == q.rank) and (p.distance == q.distance):
        return 0
    return 1

def select_parents(population, random_select=False):
    """Return two parent solutions.

    Uses k-ary tournament selection, where k individuals are selected and ranked by the
    crowding comparison operator.

    If random_select is True, randomly choose parents."""
    parents = [None, None]
    for i in range(2):
        # pick two elements of the population
        if random_select:
            parents[i] = random.choice(population)
        else:
            choices = random.sample(population, 3)
            parents[i] = sorted(choices,
                                key=functools.cmp_to_key(crowding_operator))[0]

    return parents

def make_children(parents, random_select=False):
    """Take a parent population and return an equally-sized child population."""
    children = []
    for _ in tqdm(range(len(parents) // 2), desc="Making children"):
        parent_a, parent_b = select_parents(parents, random_select=random_select)
        assert parent_a is not None
        assert parent_b is not None

        offspring = parent_a.crossover_and_mutate(parent_b)
        children += offspring

    return children

def make_adam_and_eve(population_size):
    """Makes the first generation."""
    parents = [Candidate.generate() for i in tqdm(range(population_size),
                                                  desc="Creating first parents")]
    offspring = make_children(parents, random_select=True)

    return parents, offspring

def _optimize(c):
    return c.optimize()

@profile
def evolve(graph, config, debug_output=False,
           objective_fns=[(objectives.PopulationEquality, {'key': 'pop'})]):
    # pylint: disable=R0915, W0603, R0914
    """Runs NSGA-II."""
    if 'order' not in graph:
        m = {}
        for idx, vertex in enumerate(graph):
            m[vertex] = idx
        graph.graph['order'] = m


    Candidate.master_graph = graph

    Candidate.objectives = [cls(graph, **args) for cls, args in objective_fns]
    State.objectives = Candidate.objectives

    max_generations = config.get("generations", 500)
    pop_size = config.get("population_size", 300)
    mutation_probability = config.get("mutation_probability", 0.7)
    multiprocess = config.get("multiprocess", False)
    break_on_final_gen = config.get("early_break", False)
    optimize = config.get("optimize", True)

    _data_output = {'pareto_per_gen': [],
                    'final_gen': max_generations}

    Candidate.mutation_probability = mutation_probability

    print("Starting NSGA-II. Running for {gens} generations with a population of {pop}."
          .format(gens=max_generations, pop=pop_size))

    print("Building initial population...")
    parents, offspring = make_adam_and_eve(pop_size)
    raw_combined_population = parents + offspring

    if multiprocess:
        with Pool() as p:
            # combined_population = pool.map(_optimize, raw_combined_population)
            size = pop_size * 2
            with tqdm(total=size) as pbar:
                for i, _ in tqdm(enumerate(p.imap_unordered(_optimize,
                                                            raw_combined_population))):
                    pbar.update()
    combined_population = raw_combined_population

    signal.signal(signal.SIGINT, signal.default_int_handler)
    signal.signal(signal.SIGTERM, signal.default_int_handler)

    for gen in tqdm(range(1, max_generations), "Evolving..."):
        try:
            frontiers = fast_non_dominated_sort(combined_population)
            _data_output['pareto_per_gen'].append(frontiers[0])

            print("Best frontier in generation", str(gen) + ":",
                  set([tuple(cand.scores) for cand in frontiers[0]]))
            print("Fronts", len(frontiers))

            next_parents = []
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

            parents = next_parents[:len(parents)]
            if len(set(parents)) == 1:
                _data_output['final_gen'] = gen
                if break_on_final_gen:
                    break


            raw_offspring = make_children(parents)
            if optimize:
                if multiprocess:
                    with Pool() as pool:
                        offspring = pool.map(_optimize, raw_offspring)
                else:
                    offspring = []
                    for child in tqdm(raw_offspring, "Optimizing children"):
                        offspring.append(child.optimize())
            else:
                offspring = raw_offspring

            combined_population = parents + offspring

            Candidate.mutation_probability *= 0.99
        except KeyboardInterrupt:
            print("Quitting after", gen, "generations.")
            _data_output['final_gen'] = gen
            break

    print("Finished running NSGA-II. Best frontier:",
          set([tuple(cand.scores) for cand in frontiers[0]]))
    print("Finished running NSGA-II. Best generation:", frontiers[0])

    if debug_output:
        return frontiers[0], _data_output

    return frontiers[0]

def test():
    """Testing function."""
    import matplotlib.pyplot as plt
    G = nx.OrderedGraph()
    for i in range(5):
        for j in range(3):
            G.add_node((i, j), pop=3*i + j + 1)
    for i in range(5):
        for j in range(3):
            if j < 2:
                G.add_edge((i, j), (i, j+1))
            if i < 4:
                G.add_edge((i, j), (i+1, j))

    final = evolve(G, {
        "population_size": 10
    })[0]
    new_graph = final.reconstruct_graph()

    nx.draw_networkx(new_graph, pos={n: n for n in G})
    plt.show()

if __name__ == "__main__":
    test()
