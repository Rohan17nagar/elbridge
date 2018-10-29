"""Various utility classes and methods."""
import os
from pathlib import Path
from typing import List, Set

from networkx import Graph

from elbridge.utilities.types import Component, Node


class cd:
    """Context manager for changing the current working directory."""

    def __init__(self, new_path):
        """Point this to new_path."""
        self.new_path = Path(new_path).expanduser()
        self.saved_path = None

    def __enter__(self):
        self.saved_path = Path.cwd()
        if not self.new_path.exists():
            self.new_path.mkdir(parents=True)

        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)


def dominates(a_scores: List[float], b_scores: List[float]) -> float:
    as_good = True
    better = False
    for idx in range(len(a_scores)):
        if b_scores[idx] > a_scores[idx]:
            as_good = False
            break
        elif b_scores[idx] < a_scores[idx]:
            better = True

    return as_good and better


def gradient(a_scores: List[float], b_scores: List[float]) -> float:
    return sum(a_scores[i] - b_scores[i] for i in range(len(a_scores)))


@profile
def number_connected_components(graph: Graph, component: Component) -> int:
    remaining: Set[Node] = set(component)
    count = 0

    while remaining:
        source = remaining.pop()
        frontier: Set[Node] = {source}

        while frontier:
            node: Node = frontier.pop()
            neighbors = graph[node]
            for neighbor in filter(lambda n: n in remaining, neighbors):
                remaining.remove(neighbor)
                frontier.add(neighbor)
        count += 1

    return count
