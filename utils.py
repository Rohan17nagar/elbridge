"""Various utility classes and methods."""
import os
import random

class cd:
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


def random_subset(iterator, K):
    """Picks k random elements of set using reservoir sampling."""
    result = []
    N = 0

    for item in iterator:
        N += 1
        if len(result) < K:
            result.append(item)
        else:
            s = int(random.random() * N)
            if s < K:
                result[s] = item

    return result
