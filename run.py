"""Main runner."""
import logging
import argparse
import json
from datetime import datetime

import shape
import vrdb
from utils import cd

def main(data_dir, county_config, block_config, vr_config):
    """Main function."""

    with cd(data_dir):
        county_graph = shape.create_county_graph(county_config)
        block_graph = shape.create_block_graph(block_config, county_graph)
        vrdb.annotate_block_graph(block_graph, vr_config)

# pylint: disable=C0103
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an optimal gerrymander.")
    parser.add_argument('--config', dest='config_file', default='config.json',
                        help="Load preferences from specified config file (default ./config.json). \
                        If no configuration file is found, defaults to preferences set in \
                        ./defaults.json.")

    parser.parse_args()
    with open(parser.config_file) as config_file:
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

    county_config = config.get("counties", {
        "state_code": 53,
        "directory": "wa-counties",
        "filename": "wa-counties.shp",
        "pickle_graph": True,
        "draw_graph": False,
        "draw_shapefile": False,
        "reload_graph": False
    })

    block_config = config.get("blocks", {
        "directory": "wa-blocks",
        "filename": "wa-blocks.shp",
        "pickle_graph": True,
        "draw_graph": False,
        "draw_shapefile": False,
        "reload_graph": False
    })

    vr_config = config.get("voter_registration", {
        "directory": "wa-vr-db",
        "filename": "201708_VRDB_Extract.txt"
    })

    data_directory = config.get("data_directory", "/var/local/rohan")

