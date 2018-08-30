class KeyNotFoundException(Exception):
    def __init__(self, key, data):
        super().__init__("Key {} not found in node data {}".format(key, data))


class ClassNotInitializedException(Exception):
    def __init__(self, cls):
        super().__init__("Class {} not initialized".format(cls))


class InconsistentSearchStateException(Exception):
    def __init__(self, state, out):
        super().__init__("Inconsistent search state (scores {}) and candidate (scores {})".format(
            state.scores, out.scores
        ))


class SameComponentException(Exception):
    def __init__(self, i, j, i_cmp):
        super().__init__("Vertices {} and {} are in the same component {}".format(i, j, i_cmp))


class IncompleteHypotheticalsException(Exception):
    def __init__(self, edge):
        super().__init__("Edge {} not in hypotheticals set for graph".format(edge))
