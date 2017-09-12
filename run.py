"""Main runner."""
import os
import logging
import argparse

import shape
import networkx as nx

# import climber
import vrdb

def main(log_level=30, data_prefix='data', shape_name='state_shapes', force_reload_graph=False):
    """Main function."""
    logging.basicConfig(level=log_level, format=
                        "[%(levelname)s %(asctime)s] %(filename)s@%(funcName)s [line %(lineno)d]: \
                        %(message)s")
    # filename="{}.log".format(datetime.now().isoformat()))

    in_dir = os.path.join(data_prefix, shape_name)

    if not force_reload_graph and os.path.exists(os.path.join(in_dir, shape_name + ".pickle")):
        logging.info("Pickle found at %s", os.path.join(in_dir, shape_name + ".pickle"))
        G = nx.read_gpickle(os.path.join(in_dir, shape_name + ".pickle"))
        logging.info("Finished reading pickle")
    else:
        logging.info("No pickle found, reading from file")
        G = shape.create_graph(in_dir, shape_name, pickle=True)

    node = vrdb.build_block_map(G, address_dir="/var/local/rohan/wa-vr-db", address_file="vrdb_trunc.txt")
    print(node)
    # climber.find_frontier(G, 5, samples=samples)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an optimal gerrymander.")

    parser.add_argument('--log', help='Default logging level.',
                        default='WARN', choices=['DEBUG', 'INFO', 'WARN', 'ERROR', 'CRITICAL'])
    parser.add_argument('--reload', help='Overwrite pickle.', action="store_true")

    parser.add_argument('--dir', help='Name of shapefiles.', default='state_shapes')
    parser.add_argument('--data', help='Data directory.', default='data')

    args = parser.parse_args()

    main(log_level=getattr(logging, args.log.upper(), None), data_prefix=args.data,
         shape_name=args.dir, force_reload_graph=args.reload)
