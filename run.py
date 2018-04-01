"""Main runner."""

import logging
import argparse
import json
from datetime import datetime

import builtins
import matplotlib

# hack to modify @profile for non-kernprof use
try:
    builtins.profile
except AttributeError:
    def profile(func):
        """Passthrough."""
        return func
    builtins.profile = profile

# prevent X11 errors on matplotlib graph creation
matplotlib.use('Agg')

import shape
import annotater
from utils import cd
import evaluation

def main(data_dir, parameter_config, block_group_config, block_config,
         county_config, precinct_config, data_config):
    """Main function."""

    with cd(data_dir):
        county_graph = shape.create_county_graph(county_config)
        annotater.initialize_county_graph(county_config, precinct_config, data_config,
                                          county_graph)

        block_group_graph = shape.create_block_group_graph(block_group_config)
        annotater.initialize_block_group_graph(block_group_config, precinct_config, data_config,
                                               county_graph, block_group_graph)

        print("Finished reading in all graphs. Leaving data directory.")

    best_solutions = evaluation.eval_graph(block_group_graph, "Block Group Graph", "bgg", config=parameter_config)

    print("Finished evolution.")

    final = best_solutions[0]
    final.plot(save=True)

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

    parameter_configuration = config.get("parameters", {
        "mutation_probability": 0.7,
        "generations": 500,
        "population_size": 300
    })

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

    voting_data_configuration = config.get("elections", {
        "directory": "wa-election-data",
        "filename": "election-data.csv"
    })

    data_directory = config.get("data_directory", "/var/local/rohan")
    main(data_directory, parameter_configuration, block_group_configuration,
         block_configuration, county_configuration, precinct_configuration,
         voting_data_configuration)
