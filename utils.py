"""Various utility classes and methods."""
import os
import signal
from collections import defaultdict
import networkx as nx

class cd:
    # pylint: disable=invalid-name, too-few-public-methods
    """Context manager for changing the current working directory."""
    def __init__(self, new_path):
        """Point this to new_path."""
        self.new_path = os.path.expanduser(new_path)
        self.saved_path = None

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)


class InterruptableRegion(object):
    """Handles SIGINT interrupts."""
    def __init__(self, sig=signal.SIGINT):
        self.sig = sig
        self.interrupted = False
        self.released = False
        self.original_handler = None

    def __enter__(self):
        self._validate_region_start()
        self._store_signal_default_handler()

        def _signal_invoked_new_handler(signum, frame):
		    # pylint: disable=unused-argument
            self._release()
            self.interrupted = True

        signal.signal(self.sig, _signal_invoked_new_handler)

        return self

    def __exit__(self, etype, value, tb):
        self._release()

    def _validate_region_start(self):
        if self.interrupted or self.released or self.original_handler:
            raise RuntimeError("An interruptable region can only be used once")

    def _release(self):
        if not self.released:
            self._reset_signal_default_handler()
            self.released = True

    def _store_signal_default_handler(self):
        self.original_handler = signal.getsignal(self.sig)

    def _reset_signal_default_handler(self):
        signal.signal(self.sig, self.original_handler)

def chromosome_to_components(graph, vertex_set):
    """Converts a vertex set to components."""
    component_lists = defaultdict(list)
    for v, data in graph.nodes(data=True):
        comp = get_component(vertex_set, graph, v)
        component_lists[comp].append((v, data))
    return component_lists
    # vertex_list = list(graph.nodes(data=True))

    # for idx, comp_idx in enumerate(vertex_set):
        # vertex = vertex_list[idx]
        # component_lists[comp_idx].append(vertex)
    # return component_lists

def get_index(graph, vertex):
    """Take a vertex, find its index in the graph, and return that position in
    the chromosome."""
    assert "order" in graph.graph
    return graph.graph['order'][vertex]

def get_component(chromosome, graph, vertex):
    """Take a vertex, find its index in the graph, and return that position in
    the chromosome."""
    return chromosome[get_index(graph, vertex)]
