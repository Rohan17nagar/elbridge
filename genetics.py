# pylint: disable=C0103
"""Genetic algorithm stuff."""

import random
import functools

from disjointset import DisjointSet
import objectives
import shape

import networkx as nx
from tqdm import tqdm
import matplotlib.pyplot as plt

MASTER_GRAPH = None
OBJECTIVES = None
MUT_PB = None
DISTRICTS = objectives.DISTRICTS

tqdm = lambda x, *y: x

class Candidate():
    """
    Encapsulates a candidate solution.

    The chromosome is given by an |E|-length real array A, where A[i] is the order in which edge i 
    is added to the graph.
    """
    i = 0
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

        self.objectives = [objective(self) for objective in OBJECTIVES]
        
        self.name = Candidate.i
        Candidate.i += 1

    def __repr__(self):
        return str(self.name) + " (" + str(self.objectives) + ")"

    def dominates(self, other):
        """
        Returns True if p dominates q.

        Domination is defined as a partial ordering < on solutions, where
        for some objectives f1, f2, ..., fm, p < q iff for all i <= m fi(p) >= fi(q).
        """
        for i in range(len(self.objectives)):
            if self.objectives[i] <= other.objectives[i]:
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
        if random.random() < MUT_PB:
            element = random.randint(0, len(self.chromosome)-1)
            self.chromosome[element] = random.random()

    def reconstruct_graph(self):
        """Take a chromosome and return the corresponding graph.

        chromosome[i] corresponds to the priority of edge i.
        """
        master = MASTER_GRAPH
        order = sorted([(priority, idx) for idx, priority in enumerate(self.chromosome)],
                       reverse=True)
        disjoint_set = DisjointSet(master.nodes())

        H = nx.Graph()
        H.add_nodes_from(master.nodes(data=True))

        for _, i in order:
            u, v = master.edges()[i]
            H.add_edge(u, v)
            disjoint_set.union(u, v)
            # print(u, v, disjoint_set)
            # nx.draw_networkx(H, pos={node: list(data.get('shape').centroid.coords)[0]
            #                          for node, data in H.nodes(data=True)})
            # plt.show()

            if len(disjoint_set) == DISTRICTS:
                break
        return H

def fast_non_dominated_sort(population):
    """Take a population P and sort it into fronts F1, F2, ..., Fn."""
    fronts = [[]]
    print(population)

    for p in tqdm(population, "Building domination sets..."):
        for q in population:
            if p == q:
                continue

            # print(p, q, p.dominates(q), q.dominates(p))

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
        next_front = []
        for p in fronts[i]:
            for q in p.dominated_set:
                q.domination_count -= 1
                if q.domination_count == 0:
                    q.rank = i + 1
                    next_front.append(q)

        i += 1
        fronts.append(next_front)

    print(fronts)
    return fronts[:-1]

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

    for _ in tqdm(range(population_size), "Building initial population..."):
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
    for _ in tqdm(range(0, len(parents), 2), "Building next generation..."):
        [parent_a, parent_b] = select_parents(parents)
        offspring = parent_a.crossover(parent_b)
        for child in offspring:
            child.mutate()

        children += offspring
    return children

def run(block_graph, max_generations=1000, pop_size=50, mutation_probability=0.02):
    """Runs NSGA-II."""
    # create first generation
    global MASTER_GRAPH
    MASTER_GRAPH = block_graph

    global OBJECTIVES
    OBJECTIVES = [obj(block_graph) for obj in objectives.OBJECTIVES]

    global MUT_PB
    MUT_PB = mutation_probability

    parents = make_adam_and_eve(block_graph, pop_size)
    offspring = make_children(parents)
    print("Finished building initial population.")

    for _ in tqdm(range(1, max_generations), "Evolving..."):
        combined_population = parents + offspring
        frontiers = fast_non_dominated_sort(combined_population)
        print(len(combined_population))

        next_parents = []
        remaining_slots = len(parents)
        i = 0
        
        print("Building next frontier...")
        print([len(frontier) for frontier in frontiers], sum([len(f) for f in frontiers]))
        while i < len(frontiers):
            frontier = frontiers[i]
            if remaining_slots < len(frontier):
                # continue until you can't add any more
                break

            crowding_distance_assignment(frontier)
            next_parents += frontier

            remaining_slots -= len(frontier)
            i += 1

        print(remaining_slots, len(frontiers), i)

        if remaining_slots != 0:
            # fill the remaining slots with the best elements of frontier[i]
            # this sorts x = (r1, d1) and y = (r2, d2) as x < y if r1 < r2 or r1 == r2 and d1 > d2
            print(i, len(frontiers))
            frontiers[i].sort(key=functools.cmp_to_key(crowding_operator))
            next_parents += frontiers[i][:remaining_slots]

        print("Finished building next frontier.")

        parents = next_parents
        print("Making children...")
        offspring = make_children(parents)
        print("Finished making children.")
        print(len(parents), len(offspring), "\n\n")

    frontiers = fast_non_dominated_sort(parents + offspring)
    best_frontier = frontiers[0]

    for chromosome in best_frontier:
        plot_chromosome(chromosome)

def plot_chromosome(chromosome):
    """Plots a chromosome."""
    graph = chromosome.reconstruct_graph()
    print(len(graph))
    title = "Chromosome (" \
            + "; ".join(["{name}: {value}".format(name=str(fn),
                                                  value=fn(chromosome)) for fn in OBJECTIVES]) \
            + ")"
    shapes = []
    for component in nx.connected_component_subgraphs(graph):
        color = (random.random(), random.random(), random.random())
        shapes += [(data.get('shape'), color) for _, data in component.nodes(data=True)]

    shape.plot_shapes(shapes, title=title)
    