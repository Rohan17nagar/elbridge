# pylint: disable=C0103, C0200
"""Local search."""
import random
from typing import Optional, List

from tqdm import tqdm

from elbridge.evolution.chromosome import Chromosome
from elbridge.evolution.hypotheticals import HypotheticalSet
from elbridge.evolution.search_state import SearchState
from elbridge.types import Edge


@profile
def make_step(state: SearchState, edge: Edge) -> Optional[SearchState]:
    i, j = edge

    new_state = SearchState(state.hypotheticals, state.chromosome)

    new_state.connect_vertices(i, j)
    new_state.evaluate()

    if state.dominated_by(new_state):
        return new_state

    return None


@profile
def find_best_neighbor(state: SearchState, sample_size: int = 50) -> Optional[SearchState]:
    """Find the best neighbors of this state."""
    moves = state.hypotheticals.edges
    samples = random.sample(moves, min(len(moves), sample_size))

    best_state = None
    best_gradient = float('-inf')
    for move in samples:
        new_state = make_step(state, move)
        if new_state:
            new_gradient = state.gradient(new_state)
            if new_gradient > best_gradient:
                best_state = new_state
                best_gradient = new_gradient
            else:
                del new_state

    return best_state


@profile
def optimize(hypotheticals: HypotheticalSet, chromosome: Chromosome, scores: Optional[List[float]] = None,
             pos: int = 0, steps: int = 1000, sample_size: int = 100) -> SearchState:
    """Take a solution and return a nearby local maximum."""
    state = SearchState(hypotheticals, chromosome, scores=scores)

    for _ in tqdm(range(steps), "Taking steps", position=pos):
        new_state = find_best_neighbor(state, sample_size)
        if new_state is None:
            return state

        state = new_state

    return state
