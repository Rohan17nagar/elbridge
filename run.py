import shape
from shapely.ops import cascaded_union
import networkx as nx

import os
import logging
import argparse

from datetime import datetime

import climber

def main(log_level=30, samples=100, steps=100,
  data_prefix='data', shape_name='state_shapes', force_reload_graph=False):
  logging.basicConfig(level=log_level,
    format="[%(levelname)s %(asctime)s] %(filename)s@%(funcname)s [line %(lineno)d]: %(message)s",
    filename="{}.log".format(datetime.now().isoformat()))

  in_dir = os.path.join(data_prefix, shape_name)

  if not force_reload_graph and os.path.exists(os.path.join(in_dir, shape_name + ".pickle")):
    logging.info("Pickle found at %s", os.path.join(in_dir, shape_name + ".pickle"))
    G = nx.read_gpickle(os.path.join(in_dir, shape_name + ".pickle"))
    logging.info("Finished reading pickle")
  else:
    logging.info("No pickle found, reading from file")
    G = shape.create_graph(in_dir, shape_name, pickle=True)

  climber.find_frontier(G, 5, samples=samples)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Generate an optimal gerrymander.")

  parser.add_argument('--log', help='Default logging level.',
    default='WARN', choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'])
  parser.add_argument('--reload', help='Overwrite pickle.', action="store_true")

  parser.add_argument('--dir', help='Name of shapefiles.', default='state_shapes')
  parser.add_argument('--data', help='Data directory.', default='data')

  parser.add_argument('--samples', help='Number of starting positions from which to run hill-climbing.',
    default=100, type=int)
  parser.add_argument('--steps', help='Steps per run.', default=100, type=int)


  args = parser.parse_args()

  _log_level = args.log
  log_level = getattr(logging, _log_level.upper(), None)

  samples = args.samples
  steps = args.steps

  shape_dir = args.dir
  data_dir = args.data

  reload_graph = args.reload

  main(samples=samples, steps=steps, log_level=log_level, data_prefix=data_dir, shape_name=shape_dir,
    force_reload_graph=reload_graph)