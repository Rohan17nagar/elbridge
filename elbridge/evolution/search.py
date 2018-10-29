"""Local search."""
import random
from multiprocessing.pool import Pool
from typing import Optional

from tqdm import tqdm

from elbridge.evolution.chromosome import Chromosome

# use this to mute tqdm
tqdm = lambda x, *y, **z: x


def find_best_neighbor_simple(state: Chromosome, sample_size: int = 100) -> Optional[Chromosome]:
    moves = state.get_hypotheticals().edges
    samples = random.sample(moves, min(len(moves), sample_size))

    best_state = None
    best_gradient = float('-inf')

    for move in samples:
        new_state = state.connect_vertices(move)
        new_gradient = state.gradient(new_state)

        if new_state.dominates(state) and new_gradient > best_gradient:
            best_state = new_state
            best_gradient = new_gradient

    return best_state


def find_best_neighbor(state: Chromosome, sample_size: int = 100) -> Optional[Chromosome]:
    """Find the best neighbors of this state."""
    moves = state.get_hypotheticals().edges
    samples = random.sample(moves, min(len(moves), sample_size))

    with Pool(processes=4) as p:
        new_states = p.map(state.connect_vertices, samples)
        try:
            return max(filter(lambda ns: ns.dominates(state), new_states), key=lambda ns: state.gradient(ns))
        except ValueError:
            return None


def optimize(chromosome: Chromosome, pos: int = 0, steps: int = 100, sample_size: int = 100) -> Chromosome:
    """Take a solution and return a nearby local maximum."""
    state = chromosome

    for _ in tqdm(range(steps), "Taking steps", position=pos):
        new_state = find_best_neighbor(state, sample_size=sample_size)
        if new_state is None:
            return state

        state = new_state

    return state
