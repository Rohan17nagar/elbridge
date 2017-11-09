# pylint: disable=C0103
"""Genetic algorithm stuff."""

import random
import functools
from multiprocessing import Pool
from datetime import datetime

from disjointset import DisjointSet
import shape
import objectives
import search

import networkx as nx
from tqdm import tqdm

MASTER_GRAPH = None
OBJECTIVES = None
MUT_PB = None
POOL = None
DISTRICTS = objectives.DISTRICTS

# use this to mute tqdm
# tqdm = lambda x, *y: x

class Candidate():
    """
    Encapsulates a candidate solution.

    The chromosome is given by an |E|-length real array A, where A[i] is the order in which edge i 
    is added to the graph.
    """
    i = 0
    def __init__(self, edge_set, copy=False, mutation_probability=0.7):
        self.chromosome = edge_set

        # set of candidates this candidate dominates
        self.dominated_set = set()
        # number of candidates this candidate is dominated by
        self.domination_count = 0
        # this candidate's front
        self.rank = 0
        # distance to other candidates on front
        self.distance = 0

        self.mutation_probability = mutation_probability

        self.graph = None
        self.hypotheticals = set()

        if copy:
            self.objectives = []
            self.name = None
        else:
            self.objectives = [objective(self.reconstruct_graph()) for objective in OBJECTIVES]
            self.name = Candidate.i
            Candidate.i += 1

    def __repr__(self):
        return str(self.name) + " (" + str(self.objectives) + ")"

    def __eq__(self, other):
        return self.chromosome == other.chromosome
        # this_graph = self.reconstruct_graph()
        # other_graph = other.reconstruct_graph()

        # return this_graph.edges() == other_graph.edges()

    def copy(self):
        """Returns a copy of this chromosome."""
        copy = Candidate(self.chromosome, copy=True)
        copy.objectives = self.objectives
        copy.name = self.name
        copy.graph = self.graph
        return copy

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
        if random.random() < self.mutation_probability:
            element = random.randint(0, len(self.chromosome)-1)
            self.chromosome[element] = random.random()

    def reconstruct_graph(self):
        """Take a chromosome and return the corresponding graph.

        chromosome[i] corresponds to the priority of edge i.
        """
        if self.graph:
            return self.graph

        master = MASTER_GRAPH
        order = sorted([(priority, idx) for idx, priority in enumerate(self.chromosome)],
                       reverse=True)
        disjoint_set = DisjointSet(master.nodes())

        H = nx.Graph()
        H.add_nodes_from(master.nodes(data=True))
        i = 0

        hypotheticals = set(master.edges())

        for _, i in order:
            u, v = list(master.edges())[i]
            hypotheticals.remove((u, v))
            H.add_edge(u, v)
            disjoint_set.union(u, v)

            if len(disjoint_set) == DISTRICTS:
                break

        components = nx.connected_components(H)
        for component in components:
            original_subgraph = master.subgraph(component)
            for edge in original_subgraph.edges():
                if not H.has_edge(*edge):
                    # this is an edge in the original inside a component
                    H.add_edge(*edge)
                    hypotheticals.remove(edge)

        self.hypotheticals = hypotheticals

        assert len(disjoint_set) == DISTRICTS, disjoint_set

        self.graph = H
        return H

    def plot(self):
        """Plots a chromosome."""
        graph = self.reconstruct_graph()
        title = "Chromosome (" \
                + "; ".join(["{name}: {value}"
                             .format(name=str(OBJECTIVES[idx]), value=self.objectives[idx])
                             for idx in range(len(OBJECTIVES))]) + ")"
        shapes = []

        print("Goal size:", sum([data.get('pop')
                                 for _, data in graph.nodes(data=True)])/DISTRICTS)

        for i, component in enumerate(nx.connected_component_subgraphs(graph)):
            color = (random.random(), random.random(), random.random())
            shapes += [(data.get('shape'), color) for _, data in component.nodes(data=True)]

            print("Component", i)
            print("\n".join(["\tCounty {name}: population {pop}"
                             .format(name=node, pop=data.get('pop'))
                             for node, data in component.nodes(data=True)]))
            print("Total population:",
                  sum([data.get('pop') for _, data in component.nodes(data=True)]))
            print()

        shape.plot_shapes(shapes, title=title)

    def to_block_level(self, block_graph):
        """Given a block graph, only keep connections between blocks in the same component."""
        county_graph = self.reconstruct_graph()
        county_districts = nx.connected_components(county_graph)

        # county --> index of district
        county_to_district = {}
        for i, component in enumerate(county_districts):
            for node in component:
                county_to_district[node] = i
        
        output = block_graph.copy()

        hypotheticals = set()
        
        # remove edge (i,j) if c2d[i] != c2d[j]
        edges = list(output.edges())
        for i, j in edges:
            county = lambda n: n[:5]
            if county_to_district[county(i)] != county_to_district[county(j)]:
                output.remove_edge(i, j)
                hypotheticals.add((i, j))

        return output, hypotheticals

    def optimize(self):
        """Local search."""
        graph = self.reconstruct_graph()
        hypotheticals = self.hypotheticals

        evolved_graph, evolved_hypotheticals, scores = search.optimize(graph,
                                                                       hypotheticals,
                                                                       steps=20)
        self.graph = evolved_graph
        self.hypotheticals = evolved_hypotheticals
        self.objectives = scores


# @profile
def _assign_rank(population, elem):
    p = elem.copy()
    tqdm = lambda a, *x: a
    for i, q in tqdm(enumerate(population)):
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

    pool = POOL

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
    for idx, _ in enumerate(OBJECTIVES):
        frontier.sort(key=lambda p, idx=idx: p.objectives[idx])

        # the boundary points for each objective should always be preserved
        frontier[0].distance = float('inf')
        frontier[-1].distance = float('inf')

        for i, _ in enumerate(frontier[1:-1]):
            frontier[i].distance += (frontier[i+1].objectives[idx] \
                - frontier[i-1].objectives[idx]) \
                / (OBJECTIVES[idx].max_value - OBJECTIVES[idx].min_value)

def crowding_operator(p, q):
    """Return 1 if p << q; -1 otherwise. Used to sort last frontier."""
    if (p.rank < q.rank) or ((p.rank == q.rank) and (p.distance > q.distance)):
        return -1
    return 1

def make_adam_and_eve(graph, population_size):
    """Makes the first generation."""
    num_edges = len(graph.edges())
    parents = []

    pool = POOL
    parents = pool.map(Candidate, [[random.random() for i in range(num_edges)] \
        for _ in range(population_size)])

    # for _ in range(population_size):
    #     chromosome = [random.random() for i in range(num_edges)]
    #     parents.append(Candidate(chromosome))

    return parents

def select_parents(population):
    """Return two parent solutions.

    Uses binary tournament selection, where two individuals are selected and ranked by the 
    crowding comparison operator."""
    parents = [None, None]
    for i in range(2):
        # pick two elements of the population
        # parents[i] = max(random.sample(population, 2),
        #                  key=functools.cmp_to_key(crowding_operator))
        [parent_a, parent_b] = random.sample(population, 2)
        if crowding_operator(parent_a, parent_b) == -1:
            parents[i] = parent_a
        else:
            parents[i] = parent_b

    return parents

def _make_children(parents):
    [parent_a, parent_b] = parents
    offspring = parent_a.crossover(parent_b)
    for child in offspring:
        child.mutate()

    return offspring

def make_children(parents):
    """Take a parent population and return an equally-sized child population."""
    pool = POOL
    children = pool.map(_make_children, [select_parents(parents)] * (len(parents) // 2))
    return [child for sublist in children for child in sublist]

def evolve(graph, max_generations=100, pop_size=300, mutation_probability=0.7):
    # pylint: disable=R0915, W0603, R0914
    """Runs NSGA-II."""
    global MASTER_GRAPH
    MASTER_GRAPH = graph

    global OBJECTIVES
    OBJECTIVES = [obj(graph) for obj in objectives.OBJECTIVES]

    global MUT_PB
    MUT_PB = mutation_probability

    global POOL
    POOL = Pool(4)

    print("Starting NSGA-II. Running for {gens} generations with a population of {pop}."
          .format(gens=max_generations, pop=pop_size))

    stime = datetime.now()
    print("Building initial population...")
    parents = make_adam_and_eve(graph, pop_size)
    offspring = make_children(parents)
    etime = datetime.now()
    print("Finished building initial population. Time:", etime - stime)

    best_scores = []

    for gen in tqdm(range(1, max_generations), "Evolving..."):
        try:
            print("######### START OF GENERATION", gen + 1, "########")
            gen_stime = datetime.now()
            combined_population = parents + offspring
            sort_stime = datetime.now()
            frontiers = fast_non_dominated_sort(combined_population)
            sort_etime = datetime.now()
            print("Finished sorting in", str(sort_etime - sort_stime))

            print("Best element in generation", str(gen) + ":", str(frontiers[0][0]))
            best_scores.append(frontiers[0][0].objectives)
            
            next_parents = []
            remaining_slots = len(parents)
            i = 0
            
            print("Building next generation...")
            while i < len(frontiers):
                frontier = frontiers[i]
                if remaining_slots < len(frontier):
                    # continue until you can't add any more
                    break

                crowding_distance_assignment(frontier)
                next_parents += frontier

                remaining_slots -= len(frontier)
                i += 1

            print("Used", i, "frontiers.", remaining_slots, "slots remaining.")
            if remaining_slots != 0:
                # fill the remaining slots with the best elements of frontier[i]
                # this sorts x = (r1, d1) and y = (r2, d2) as x < y
                # if r1 < r2 or r1 == r2 and d1 > d2
                frontiers[i].sort(key=functools.cmp_to_key(crowding_operator))
                next_parents += frontiers[i][:remaining_slots]

            print("Finished building new parents.")

            parents = next_parents

            print("Making children...")
            child_stime = datetime.now()
            offspring = make_children(parents)
            # for child in tqdm(offspring, desc="Optimizing"):
            #     child.optimize()
            child_etime = datetime.now()
            print("Finished making children in", str(child_etime - child_stime))
            gen_etime = datetime.now()
            print("######## END OF GENERATION", gen + 1,
                  "(time: " + str(gen_etime - gen_stime) + ") ########")
            MUT_PB *= 0.99
        except KeyboardInterrupt:
            # stops at current generation
            break

    POOL.close()
    POOL.join()

    print()
    print("Finished running NSGA-II. Best candidate:", frontiers[0][0])

    # frontiers[0][0].plot()

    return frontiers[0]
    
def test():
    """Testing function."""
    graph = nx.grid_graph([3, 3])
    evolve(graph)

if __name__ == "__main__":
    test()
