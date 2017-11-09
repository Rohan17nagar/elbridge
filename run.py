"""Main runner."""
import logging
import argparse
import json
from datetime import datetime
import random
import networkx as nx

import shape
import annotater
from utils import cd
import genetics
import search

def main(data_dir, block_group_config, block_config, county_config,
         precinct_config):
    """Main function."""

    with cd(data_dir):
        logging.debug("Creating block group graph...")
        block_group_graph = shape.create_block_group_graph(block_group_config)
        logging.debug("Block group graph created.")

        logging.debug("Annotating block group graph with precincts...")
        annotater.add_precincts_bg(block_group_config, precinct_config, block_group_graph)
        logging.debug("Block group graph annotated.")

        logging.debug("Creating block graph...")
        block_graph = shape.create_block_graph(block_config, block_group_graph)
        logging.debug("Block group created.")

        logging.debug("Annotating block graph with precincts...")
        annotater.add_precincts_block(block_config, precinct_config,
                                      block_graph, block_group_graph)
        logging.debug("Block group annotated.")

        annotater.add_census_data_block(block_config, block_graph)

        county_graph = shape.create_county_graph(county_config)
        annotater.add_census_data(county_config, county_graph)

        print("Finished reading in all graphs.")

        best_solutions = genetics.evolve(county_graph)
        for soln in best_solutions:
            graph, hypotheticals = soln.to_block_level(block_graph)
            graph, hypotheticals, scores = search.optimize(graph, hypotheticals)

            title = "Chromosome (" \
                + "; ".join(["{value}"
                             .format(value=scores[idx])
                             for idx in range(len(scores))]) + ")"
            shapes = []
            count = 0

            for i, component in enumerate(nx.connected_component_subgraphs(graph)):
                color = (random.random(), random.random(), random.random())
                shapes += [(data.get('shape'), color) for _, data in component.nodes(data=True)]

                print("Component", i)
                # print("\n".join(["\tCounty {name}: population {pop}"
                #                  .format(name=node, pop=data.get('pop'))
                #                  for node, data in component.nodes(data=True)]))
                print("Total population:",
                      sum([data.get('pop') for _, data in component.nodes(data=True)]))
                print()
                count += 1

            print("Goal size:", sum([data.get('pop')
                                     for _, data in graph.nodes(data=True)])/count)

            shape.plot_shapes(shapes, title=title)



# pylint: disable=C0103
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an optimal gerrymander.")
    parser.add_argument('--config', dest='config_file', default='config.json',
                        help="Load preferences from specified config file (default ./config.json). \
                        If no configuration file is found, defaults to preferences set in \
                        ./defaults.json.")

    args = parser.parse_args()
    with open(args.config_file) as config_file:
        config = json.load(config_file)

    # for each config block, get if key exists, else return default

    log_config = config.get("logging", {"log_level": "WARN", "store_log_file": False})
    log_level = getattr(logging, log_config.get("log_level", "WARN"), 30)
    store_log_file = log_config.get("store_log_file", False)

    if store_log_file:
        logging.basicConfig(level=log_level, format=
                            "[%(levelname)s %(asctime)s] %(filename)s@%(funcName)s (%(lineno)d): \
                            %(message)s",
                            filename="{}.log".format(datetime.now().isoformat()))
    else:
        logging.basicConfig(level=log_level, format=
                            "[%(levelname)s %(asctime)s] %(filename)s@%(funcName)s (%(lineno)d): \
                            %(message)s")

    block_group_configuration = config.get("block_groups", {
        "directory": "wa-block-groups",
        "filename": "block-groups.shp",
        "pickle_graph": True,
        "draw_graph": False,
        "draw_shapefile": False,
        "reload_graph": False
    })

    block_configuration = config.get("blocks", {
        "directory": "wa-blocks",
        "filename": "blocks.shp",
        "pickle_graph": True,
        "draw_graph": False,
        "draw_shapefile": False,
        "reload_graph": False
    })

    county_configuration = config.get("counties", {
        "directory": "wa-counties",
        "filename": "counties.shp",
        "pickle_graph": True,
        "draw_graph": False,
        "draw_shapefile": True,
        "reload_graph": False,
        "state_code": "53",
        "data": {
            "directory": "data",
            "filename": "counties.csv"
        }
    })

    precinct_configuration = config.get("precincts", {
        "directory": "wa-precincts",
        "filename": "precincts.shp",
        "pickle_graph": True,
        "draw_shapefile": False,
    })

    data_directory = config.get("data_directory", "/var/local/rohan")
    main(data_directory, block_group_configuration, block_configuration,
         county_configuration, precinct_configuration)
