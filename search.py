# pylint: disable=C0103, C0200
"""Local search."""

from collections import defaultdict
import random
import pprint

import networkx as nx
from toposort import toposort
import matplotlib.pyplot as plt
from tqdm import tqdm

from objectives import OBJECTIVES, DISTRICTS

def to_input(candidates):
    """Take a set of candidates and find dependencies."""
    # candidate x is dominated by candidates output[x]
    output = {i : set() for i in range(len(candidates))}
    for i, cand in enumerate(candidates):
        _, _, scores, _ = cand
        for j, o_cand in enumerate(candidates):
            _, _, o_scores, _ = o_cand

            if dominates(scores, o_scores):
                output[j].add(i)
    return output

def dominates(this_scores, other_scores):
    """Returns true if this dominates other."""
    as_good = True
    better = False
    for idx in range(len(this_scores)):
        if this_scores[idx] < other_scores[idx]:
            as_good = False
            break
        elif this_scores[idx] > other_scores[idx]:
            better = True

    return as_good and better

def draw_and_highlight(block_graph, *nodes):
    index = lambda node: list(block_graph.nodes()).index(node)
    colors = ['r'] * len(block_graph)
    for i in nodes:
        colors[index(i)] = 'b'
    nx.draw_networkx(block_graph,
                     pos={node: list(data.get('shape').centroid.coords)[0] \
                          for node, data in block_graph.nodes(data=True)},
                     node_color=colors)
    plt.show()

@profile
def optimize(block_graph, hypotheticals, steps=1000, sample_size=1000):
    """Take a solution and return a nearby local maximum."""

    objectives = [objective(block_graph) for objective in OBJECTIVES]

    for _ in range(steps):
        candidates = []

        scores = [objective(block_graph) for objective in objectives]

        for i, j in random.sample(hypotheticals, min(len(hypotheticals), sample_size)):
            
            if nx.has_path(block_graph, i, j):
                draw_and_highlight(block_graph, i, j)
                raise Exception()

            adds = set() # everything added to hypotheticals
            removes = set() # everything removed from hypotheticals
            
            # get the neighbors of j
            j_edges = list(block_graph.edges(j))
            for edge in j_edges:
                # remove them from the graph
                block_graph.remove_edge(*edge)

                # add them to the hypothetical set
                hypotheticals.add(edge)
                adds.add(edge)

            # add (i, j) to graph
            block_graph.add_edge(i, j)

            # remove (i, j) from hypotheticals
            hypotheticals.remove((i, j))
            removes.add((i, j))

            # add (i', j) to graph, where i' is in the cc of i and (i', j) is in hypotheticals
            for node in nx.node_connected_component(block_graph, i):
                if (node, j) in hypotheticals:
                    block_graph.add_edge(node, j)
                    hypotheticals.remove((node, j))
                    removes.add((node, j))
                elif (j, node) in hypotheticals:
                    block_graph.add_edge(j, node)
                    hypotheticals.remove((j, node))
                    removes.add((j, node))

            if nx.number_connected_components(block_graph) == DISTRICTS:
                # evaluate
                cand_scores = [objective(block_graph) for objective in objectives]

                if dominates(cand_scores, scores):
                    # print("Dominator found!", "old:", scores, "new:", cand_scores)
                    candidates.append((block_graph.copy(), hypotheticals.copy(),
                                       cand_scores, (i, j)))

            hypotheticals = hypotheticals.union(removes).difference(adds)
            block_graph.add_edges_from(adds)
            block_graph.remove_edges_from(removes)

        if not candidates:
            return block_graph, hypotheticals, scores
        # print(len(candidates))

        # candidates now contains every potential step
        # sort it into frontiers
        frontiers = list(toposort(to_input(candidates)))
        if not frontiers:
            pprint.pprint(candidates)

        # randomly choose something from the best frontier
        block_graph, hypotheticals, scores, nodes = candidates[random.choice(tuple(frontiers[0]))]
        # draw_and_highlight(block_graph, *nodes)

    return block_graph, hypotheticals, scores








