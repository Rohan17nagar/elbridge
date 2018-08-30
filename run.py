"""Main runner."""

import argparse
import json
import logging
from datetime import datetime

import matplotlib

from elbridge.runners.runner import evaluate

# prevent X11 errors on matplotlib graph creation
matplotlib.use('Agg')


def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate an optimal gerrymander.")
    parser.add_argument(
        '--config', dest='config_file', default='config.json',
        help=("Load preferences from specified config file (default ./config.json). "
              "If no configuration file is found, defaults to preferences set in "
              "./defaults.json.")
    )
    parser.add_argument(
        '--reload-only', dest='reload_only', action='store_true', default=False,
        help="Reload graphs only. Don't run evolution.")

    args = parser.parse_args()
    with open(args.config_file) as config_file:
        config = json.load(config_file)

    return config, args.reload_only


def get_config_dicts(config):
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

    return {
        'params': parameter_configuration,
        'block_group': block_group_configuration,
        'block': block_configuration,
        'county': county_configuration,
        'precinct': precinct_configuration,
        'voting_data': voting_data_configuration,
    }


def setup_logging(config):
    log_config = config.get("logging", {"log_level": "WARN", "store_log_file": False})
    log_level = getattr(logging, log_config.get("log_level", "WARN"), 30)
    store_log_file = log_config.get("store_log_file", False)

    if store_log_file:
        logging.basicConfig(
            level=log_level, format="[%(levelname)s %(asctime)s] %(filename)s@%(funcName)s (%(lineno)d): %(message)s",
            filename="{}.log".format(datetime.now().isoformat())
        )
    else:
        logging.basicConfig(
            level=log_level, format="[%(levelname)s %(asctime)s] %(filename)s@%(funcName)s (%(lineno)d): %(message)s"
        )


# pylint: disable=C0103
if __name__ == "__main__":
    configs, reload_only = parse_arguments()
    setup_logging(configs)

    data_directory = configs.get("data_directory", "/var/local/rohan")
    evaluate(data_directory, get_config_dicts(configs), reload_only)
