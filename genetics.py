# pylint: disable=C0103
"""Genetic algorithm testing."""

import random
import functools
from disjointset import DisjointSet
import networkx as nx


OBJECTIVES = []
DISTRICTS = 3
MASTER_GRAPH = None

class Candidate():
    """
    Encapsulates a candidate solution.

    The chromosome is given by an |E|-length real array A, where A[i] is the order in which edge i 
    is added to the graph.
    """
    def __init__(self, edge_set):
        self.chromosome = edge_set

        # set of candidates this candidate dominates
        self.dominated_set = set()
        # number of candidates this candidate is dominated by
        self.domination_count = 0
        # this candidate's front
        self.rank = 0
        # distance to other candidates on front
        self.distance = 0

    def dominates(self, q):
        """
        Returns True if p dominates q.

        Domination is defined as a partial ordering < on solutions, where
        for some objectives f1, f2, ..., fm, p < q iff for all i <= m fi(p) >= fi(q).
        """
        for objective in OBJECTIVES:
            if objective(self) < objective(q):
                return False

        return True

    def crossover(self, other):
        """
        Return new Candidate objects.
        """
        # pick a random number in [0,|E|)
        split_point = random.randint(0, len(self.chromosome))

        chromosome_a = self.chromosome[:split_point] + other.chromosome[split_point:]
        chromosome_b = other.chromosome[:split_point] + self.chromosome[split_point:]

        return (Candidate(chromosome_a), Candidate(chromosome_b))        

    def mutate(self):
        """Mutate a Candidate solution in place."""
        element = random.randint(0, len(self.chromosome))
        self.chromosome[element] = random.random()

    def reconstruct_graph(self, master=MASTER_GRAPH):
        """Take a chromosome and return the corresponding graph.

        chromosome[i] corresponds to the priority of edge i.
        """
        order = sorted([(priority, idx) for idx, priority in enumerate(self.chromosome)],
                       reverse=True)
        disjoint_set = DisjointSet(range(len(master)))

        H = nx.Graph()
        H.add_nodes_from(master.nodes())

        for _, i in order:
            u, v = master.edges()[i]
            H.add_edge(u, v)
            disjoint_set.union(u, v)

            if len(disjoint_set) == DISTRICTS:
                break

        return H

def fast_non_dominated_sort(population):
    """Take a population P and sort it into fronts F1, F2, ..., Fn."""

    fronts = [[]]

    for p in population:
        for q in population:
            if p == q:
                continue

            if p.dominates(q):
                p.dominated_set.add(q)
            elif q.dominates(p):
                p.domination_count += 1

        if p.domination_count == 0:
            # this candidate is in the first front (it isn't dominated by anything)
            p.rank = 1
            fronts[0].append(p)

    i = 0
    # pylint: disable=C1801
    while len(fronts[i]) != 0:
        next_front = set()
        for p in fronts[i]:
            for q in p.dominated_set:
                q.domination_count -= 1
                if q.domination_count == 0:
                    q.rank = i + 1
                    next_front.add(q)

        i += 1
        fronts.append(list(next_front))

    return fronts

def crowding_distance_assignment(frontier):
    """Take a Pareto frontier and calculate distances between candidates."""
    for objective in OBJECTIVES:
        frontier.sort(key=objective)

        # the boundary points for each objective should always be preserved
        frontier[0].distance = float('inf')
        frontier[-1].distance = float('inf')

        for i, _ in enumerate(frontier[1:-1]):
            frontier[i].distance += (objective(frontier[i+1]) - objective(frontier[i-1])) \
                                    / (objective.max_value - objective.min_value)

def crowding_operator(p, q):
    """Return 1 if p << q; -1 otherwise. Used to sort last frontier."""
    if (p.rank < q.rank) or ((p.rank == q.rank) and (p.distance > q.distance)):
        return 1
    return -1

def make_adam_and_eve(block_graph, population_size):
    """Makes the first generation."""
    num_edges = len(block_graph.edges())
    parents = []

    for _ in range(population_size):
        chromosome = [random.random() for i in range(num_edges)]
        parents.append(Candidate(chromosome))

    return parents

def select_parents(population):
    """Return two parent solutions.

    Uses binary tournament selection, where two individuals are selected and ranked by the 
    crowding comparison operator."""
    parents = [None, None]
    for i in range(2):
        # pick two elements of the population
        [parent_a, parent_b] = random.sample(population, 2)
        if crowding_operator(parent_a, parent_b) == 1:
            parents[i] = parent_a
        else:
            parents[i] = parent_b

    return parents

def make_children(parents):
    """Take a parent population and return an equally-sized child population."""
    children = []
    while len(children) < len(parents):
        [parent_a, parent_b] = select_parents(parents)
        offspring = parent_a.crossover(parent_b)
        children += [child.mutate() for child in offspring]
    return children

def run(block_graph, max_generations=500, pop_size=10000):
    """Runs NSGA-II."""
    # create first generation
    parents = make_adam_and_eve(block_graph, pop_size)
    offspring = make_children(parents)

    for _ in range(1, max_generations):
        combined_population = parents + offspring
        frontiers = fast_non_dominated_sort(combined_population)

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

        if remaining_slots != 0:
            # fill the remaining slots with the best elements of frontier[i]
            # this sorts x = (r1, d1) and y = (r2, d2) as x < y if r1 < r2 or r1 == r2 and d1 > d2
            frontiers[i].sort(key=functools.cmp_to_key(crowding_operator))
            next_parents += frontiers[i][:remaining_slots]

        parents = next_parents
        offspring = make_children(parents)
    