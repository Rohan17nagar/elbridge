# pylint: disable=invalid-name
"""Suite of runtime evaluations. Used for research purposes."""

import random
import time
from collections import defaultdict

import matplotlib.pyplot as plt
import networkx as nx

from elbridge.evolution import objectives
from elbridge.evolution.genetics import run_nsga2


def generate_grid_test(n, m, weight_names, max_weight=50):
    """Generate grid graphs of size n x m with random integer weights."""
    graph = nx.grid_graph([m, n])
    weights = defaultdict(dict)
    sums = defaultdict(int)
    for i in range(n):
        for j in range(m):
            for k in weight_names:
                val = random.randint(1, max_weight)
                sums[k] += val
                weights[k][(i, j)] = val

    for k in weight_names:
        nx.set_node_attributes(graph, weights[k], name=k)

    return nx.freeze(graph), sums


def grid_1f(n):
    """Evaluate performance on n x n grid graphs with one weight function."""
    objectives.DISTRICTS = n
    obj_fn = [(objectives.PopulationEquality, {'key': 'a'})]
    stamp = int(time.time())
    graph, maxes = generate_grid_test(n, n, ['a'])
    filename = 'grid1f_{}x{}_{}'.format(n, n, stamp)
    title = 'Best B-Values in $G_{' + str(n) + ', ' + str(n) + '}$'

    _, data = run_nsga2(graph, config={
        "generations": 100,
        "population_size": 50,
        "early_break": False,
        "optimize": True,
        "multiprocess": False,
    }, objective_fns=obj_fn)

    fronts = data.get('pareto_per_gen', [])
    gen_scores = []
    for front in fronts:
        elem = front[0]
        gen_scores.append(elem.scores)
    plt.plot(gen_scores, 'r-', label='w/ optimization')

    plt.title(title)
    plt.xlabel('Generation')
    plt.ylabel('B-Score (max: {val})'.format(val=maxes['a']))
    plt.yscale('symlog')
    plt.legend()

    plt.savefig('out/' + filename + '.png')
    plt.cla()


def grid_2f(n):
    """Evaluate performance on n x n grid graphs with two weight functions."""
    obj_fns = [(objectives.PopulationEquality, {'key': 'a'}),
               (objectives.PopulationEquality, {'key': 'b'})]
    stamp = int(time.time())
    m = n
    graph, maxes = generate_grid_test(n, m, ['a', 'b'])
    filename = 'grid2f_{n}x{m}_{stamp}'.format(n=n, m=m, stamp=stamp)
    title = 'Pareto Frontier in $G_{' + str(n) + ', ' + str(m) + '}$'

    final_frontier, data = run_nsga2(graph, config={
        "generations": 100,
        "population_size": 50,
        "early_break": True,
        "optimize": False,
    }, objective_fns=obj_fns, debug_output=True)

    max_gen = data.get('final_gen', 100)
    final_scores = [elem.scores for elem in final_frontier]
    a_values = [score[0] for score in final_scores]
    b_values = [score[1] for score in final_scores]

    plt.scatter(a_values, b_values, color='grey', marker='o',
                label='w/o optimization ({g} gens)'.format(g=max_gen))

    final_frontier, data = run_nsga2(graph, config={
        "generations": 100,
        "population_size": 50,
        "early_break": True,
        "optimize": True,
    }, objective_fns=obj_fns, debug_output=True)

    max_gen = data.get('final_gen', 100)
    final_scores = [elem.scores for elem in final_frontier]
    a_values = [score[0] for score in final_scores]
    b_values = [score[1] for score in final_scores]

    plt.scatter(a_values, b_values, color='red', marker='o',
                label='w/ optimization ({g} gens)'.format(g=max_gen))

    plt.title(title)
    plt.xlabel('$B_a$-score (max: {val})'.format(val=maxes['a']))
    plt.xscale('symlog')
    plt.ylabel('$B_b$-score (max: {val})'.format(val=maxes['b']))
    plt.yscale('symlog')
    plt.legend()

    plt.savefig('out/' + filename + '.png')
    plt.cla()


def evaluate_graph(graph, name, short_name, config):
    obj_fns = [(objectives.PopulationEquality, {'key': 'pop'})]
    stamp = int(time.time())
    filename = '{}_{}'.format(short_name, stamp)
    title = 'Best $B$-Values in {}'.format(name)

    final_frontier, data = run_nsga2(graph, config=config, objective_fns=obj_fns)

    fronts = data.get('pareto_per_gen', [])
    gen_scores = []
    for front in fronts:
        elem = front[0]
        gen_scores.append(elem.scores)
    plt.plot(gen_scores, 'r-', label='w/ optimization')

    final_frontier[0].plot(save=True)

    plt.title(title)
    plt.xlabel('Generation')
    plt.ylabel('B-Score')
    plt.yscale('symlog')
    plt.legend()

    plt.savefig('out/' + filename + '.png')
    plt.cla()

    return final_frontier


if __name__ == "__main__":
    grid_1f(3)
