# pylint: disable=C0103
"""Disjoint-set operator."""

from collections import defaultdict

class DisjointSet():
    """Disjoint-set data structure."""

    def __init__(self, objects):
        self.weights = {obj: 0 for obj in objects}
        self.parents = {obj: obj for obj in objects}
        self.ncomps = len(objects)

    def __len__(self):
        """Return number of connected components."""
        return self.ncomps

    def __getitem__(self, obj):
        """Return the parent of obj if obj is in the structure, None otherwise."""
        if obj not in self.parents:
            # this is not in the data structure, return None
            return None

        if self.parents[obj] != obj:
            self.parents[obj] = self[self.parents[obj]]

        return self.parents[obj]

    def union(self, x, y):
        """Union x and y."""
        x_parent = self[x]
        y_parent = self[y]

        if x_parent == y_parent:
            # x and y are in the same set
            return
        if x_parent is None or y_parent is None:
            # either x or y doesn't exist in the set
            return

        self.ncomps -= 1

        if self.weights[x_parent] < self.weights[y_parent]:
            self.parents[x_parent] = y_parent
        elif self.weights[x_parent] > self.weights[y_parent]:
            self.parents[y_parent] = x_parent
        else:
            self.parents[y_parent] = x_parent
            self.weights[x_parent] += 1

    def find(self, x):
        """Wrapper for find operation. Implemented as __getitem__ as well."""
        return self[x]

    def __repr__(self):
        return str(self.get_sets()) + " " + str(len(self))

    def get_sets(self):
        """Return the disjoint sets."""
        keys = self.parents.keys()
        out = defaultdict(list)
        for key in keys:
            parent = self.find(key)
            out[parent].append(key)
        return out.values()
