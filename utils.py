"""Context manager for changing the current working directory"""
import os
class cd:
  def __init__(self, newPath):
    self.newPath = os.path.expanduser(newPath)

  def __enter__(self):
    self.savedPath = os.getcwd()
    os.chdir(self.newPath)

  def __exit__(self, etype, value, traceback):
    os.chdir(self.savedPath)

# pick k random elements of set using reservoir sampling
import random
def random_subset(iterator, K):
  result = []
  N = 0

  for item in iterator:
    N += 1
    if len( result ) < K:
      result.append( item )
    else:
      s = int(random.random() * N)
      if s < K:
        result[ s ] = item

  return result