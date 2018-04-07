"""Graph annotation helpers.

Some notation:
- bg = block group
- co = county
- bl = block
- pr = precinct
- unit = bg | co | bl
"""

import csv
import os
from collections import defaultdict

import networkx as nx
from tqdm import tqdm
from shapely.geos import TopologicalError
import fiona

import shape

def invert_precinct_map(graph):
    """Take a graph with node --> [(precinct, intersection area)] and return
    precinct --> [(node, intersection area)]."""

    pr_to_unit = defaultdict(list)
    for node, data in graph.nodes(data=True):
        assert 'precincts' in data
        prs = data.get('precincts')

        for st_code, area in prs:
            pr_to_unit[st_code].append((node, area))

    return pr_to_unit


def add_election_data(data_config, graph_config, graph):
    # pylint: disable=R0914
    """Add election data from precinct file to graph."""
    indir = graph_config.get("directory", "wa-counties")
    infile = graph_config.get("filename", "counties.shp")

    pickle = graph_config.get("pickle_graph", True)

    data_indir = data_config.get("directory", "wa-election-data")
    data_infile = data_config.get("filename", "precinct_results.csv")

    pr_to_units = invert_precinct_map(graph)
    unit_map = defaultdict(lambda: defaultdict(int))

    with open(os.path.join(data_indir, data_infile)) as data_file:
        records = csv.reader(data_file)
        next(records)

        for record in records:
            [race, county, candidate, precinct, prec_code, votes] = record
            if precinct == "Total" or prec_code == "-1":
                continue

            assert race == "President/Vice President"

            # st code of this precinct
            st_code = county + "{:08}".format(int(prec_code))
            units = pr_to_units[st_code]

            if candidate == "Hillary Clinton / Tim Kaine":
                key = 'DEM'
            elif candidate == "Donald J. Trump / Michael R. Pence":
                key = 'REP'
            else:
                # ignore third-party races
                continue

            for unit, area in units:
                # give unit area * votes votes for candidate key
                print(unit, area, unit_map)
                unit_map[unit][key] += int(area * votes)

    nx.set_node_attributes(graph, unit_map)
    if pickle:
        nx.write_gpickle(graph,
                         os.path.join(indir, infile + ".annotated_graph.pickle"))


def add_precincts_county(co_config, pr_config, co_graph):
    """Annotate county graph with precincts."""
    indir = co_config.get("directory", "wa-counties")
    infile = co_config.get("filename", "counties.shp")

    pickle = co_config.get("pickle_graph", True)

    if any(['precincts' in data for _, data in co_graph.nodes(data=True)]):
        return

    # map block group to precincts it intersects with
    county_map = defaultdict(list)

    name_map = co_graph.graph["name_map"]

    pr_shapes = shape.get_precinct_shapes(pr_config)
    for st_code in pr_shapes:
        pr_shape, pr_data = pr_shapes[st_code]
        county_name = pr_data.get('COUNTY')

        geoid = name_map[county_name]
        
        co_shape = co_graph.node[geoid].get('shape')
        pr_shape = pr_shape.buffer(0)
        co_shape = co_shape.buffer(0)
        assert pr_shape.intersection(co_shape).area / pr_shape.area >= 0.9, \
               pr_shape.intersection(co_shape).area / pr_shape.area

        county_map[geoid].append((st_code, 1))

    nx.set_node_attributes(co_graph,
                           {county: value for county, value
                            in county_map.items()},
                           name='precincts')
    if pickle:
        nx.write_gpickle(co_graph,
                         os.path.join(indir, infile + ".annotated_graph.pickle"))

def add_precincts_block_group(bg_config, pr_config, co_graph, bg_graph):
    """Match each block group in a graph to the precinct that contains it.

    This takes a block group graph, finds all precincts that intersect it, and
    stores that data in the graph.
    """
    indir = bg_config.get("directory", "wa-block-groups")
    infile = bg_config.get("filename", "block-groups.shp")

    pickle = bg_config.get("pickle_graph", True)

    if any(['precincts' in data for _, data in bg_graph.nodes(data=True)]):
        return

    # map block group to precincts it intersects with
    bg_map = defaultdict(list)

    pr_shapes = shape.get_precinct_shapes(pr_config)

    for bg_node, bg_data in tqdm(bg_graph.nodes(data=True), "Assigning block groups to precincts"):
        bg_obj = bg_data.get('shape')
        co_data = co_graph.node[bg_node[:5]]
        precs_in_co = co_data.get('precincts')

        for st_code, _ in precs_in_co:
            pr_obj, _ = pr_shapes[st_code]
            pr_obj = pr_obj.buffer(0)
            if pr_obj.intersects(bg_obj) and not pr_obj.touches(bg_obj):
                # calculate area of precinct this block group represents
                intersection = pr_obj.intersection(bg_obj)
                pct = intersection.area / pr_obj.area

                bg_map[bg_node].append((st_code, pct))

        if not bg_map[bg_node]:
            print("No precincts found for", bg_node)

    nx.set_node_attributes(bg_graph, {bg: value for bg, value in bg_map.items()},
                           name='precincts')

    if pickle:
        nx.write_gpickle(bg_graph,
                         os.path.join(indir, infile + ".annotated_graph.pickle"))

def add_precincts_block(block_config, precinct_config, block_graph, block_group_graph):
    # pylint: disable=R0914
    """
    Match each block in a graph to the precinct that contains it,
    based on its block group graph.
    """
    indir = block_config.get("directory", "wa-blocks")
    infile = block_config.get("filename", "blocks.shp")

    pickle = block_config.get("pickle_graph", True)

    if any(['precincts' in data for _, data in block_graph.nodes(data=True)]):
        return

    # map block to precincts it intersects with
    block_map = defaultdict(list)

    precinct_shapes = shape.get_precinct_shapes(precinct_config)

    count = 0

    for block_name, block_data in tqdm(block_graph.nodes(data=True),
                                       "Assigning blocks to precincts"):
        if block_name is None:
            continue

        block_group_name = block_name[:-3]
        precincts_over_block_group = block_group_graph.nodes()[block_group_name].get('precincts',
                                                                                     [])

        block_obj = block_data.get('shape')
        if block_obj is None or not block_obj.is_valid:
            count += 1
            continue

        for st_code in precincts_over_block_group:
            precinct_obj = precinct_shapes[st_code]

            if precinct_obj.intersects(block_obj) and not precinct_obj.touches(block_obj):
                try:
                    intersection_area = precinct_obj.intersection(block_obj).area
                except TopologicalError:
                    # plot_shapes([precinct_obj])
                    intersection_area = precinct_obj.buffer(0).intersection(block_obj).area
                block_map[block_name].append((st_code, intersection_area))

    nx.set_node_attributes(block_graph,
                           {block: value for block, value in block_map.items()},
                           name='precincts')

    if pickle:
        nx.write_gpickle(block_graph, os.path.join(indir, infile + ".annotated_graph.pickle"))

def add_census_data_county(config, graph):
    """Add census data to graph."""
    indir = config.get("directory")
    infile = config.get("filename")

    data_config = config.get("data", {})
    data_indir = data_config.get("directory", "data")
    data_infile = data_config.get("filename")

    remove_empty_nodes = data_config.get("remove_empty_nodes", False)

    pickle = config.get("pickle_graph", True)

    mapping = {}

    if any(['pop' in data for _, data in graph.nodes(data=True)]):
        return

    empty_nodes = []

    with open(os.path.join(indir, data_indir, data_infile)) as data_file:
        records = csv.reader(data_file)

        next(records) # skip header
        next(records) # skip plaintext header

        for record in tqdm(records, "Reading records"):
            [_, geoid, _, _, _, _, _, _, _, _, _, _pop] = record
            pop = int(_pop)
            if remove_empty_nodes and pop == 0:
                empty_nodes.append(pop)
            else:
                mapping[geoid] = pop

    assert 0 not in mapping.values()

    if remove_empty_nodes:
        graph.remove_nodes_from(empty_nodes)

    nx.set_node_attributes(graph, mapping, name='pop')

    if pickle:
        nx.write_gpickle(graph, os.path.join(indir, infile + ".annotated_graph.pickle"))

def add_census_data_block_group(config, graph):
    """Add census data to graph."""
    indir = config.get("directory")
    infile = config.get("filename")

    data_config = config.get("data", {})
    data_indir = data_config.get("directory", "data")
    data_infile = data_config.get("filename")

    remove_empty_nodes = data_config.get("remove_empty_nodes", False)

    pickle = config.get("pickle_graph", True)

    mapping = {}

    if any(['pop' in data for _, data in graph.nodes(data=True)]):
        # graph already has population data set
        return

    empty_nodes = []

    with open(os.path.join(indir, data_indir, data_infile)) as data_file:
        records = csv.reader(data_file)

        next(records) # skip header
        next(records) # skip plaintext header

        for record in tqdm(records, "Reading records"):
            [_, geoid, _, _pop, _] = record
            pop = int(_pop)
            if remove_empty_nodes and pop == 0:
                empty_nodes.append(geoid)
            else: # no need to create mapping for empty nodes if we're going to remove them anyway
                mapping[geoid] = pop

    if remove_empty_nodes:
        graph.remove_nodes_from(empty_nodes)

    nx.set_node_attributes(graph, mapping, name='pop')

    if pickle:
        nx.write_gpickle(graph, os.path.join(indir, infile + ".annotated_graph.pickle"))

def add_census_data_from_shapefile(config, graph):
    """Add census data to graph from a shapefile.
    
    For Census blocks, population isn't available in a CSV. The only option is
    to get data from a special shapefile that has as part of its data the
    population (as POP10)"""
    indir = config.get("directory")
    infile = config.get("filename")

    data_config = config.get("data", {})
    data_indir = data_config.get("directory", "data")
    data_infile = data_config.get("filename")

    remove_empty_nodes = data_config.get("remove_empty_nodes", False)

    pickle = config.get("pickle_graph", True)

    mapping = {}

    if any(['pop' in data for _, data in graph.nodes(data=True)]):
        return

    empty_nodes = []

    with fiona.open(os.path.join(indir, data_indir, data_infile)) as blocks:
        for shp in tqdm(blocks, "Reading blocks"):
            geoid = shp.get('properties', {}).get('BLOCKID10')
            pop = shp.get('properties', {}).get('POP10', 0)
            if remove_empty_nodes and pop == 0:
                empty_nodes.append(geoid)
            else:
                mapping[geoid] = pop

    if remove_empty_nodes:
        graph.remove_nodes_from(empty_nodes)

    nx.set_node_attributes(graph, mapping, name='pop')

    if pickle:
        nx.write_gpickle(graph, os.path.join(indir, infile + ".annotated_graph.pickle"))

def initialize_county_graph(co_config, pr_config, data_config, co_graph):
    """Initialize county graph."""
    add_census_data_county(co_config, co_graph)
    # add_precincts_county(co_config, pr_config, co_graph)
    # add_election_data(data_config, co_config, co_graph)

def initialize_block_group_graph(bg_config, pr_config, data_config, ct_graph, bg_graph):
    """Initialize block group graph."""
    add_census_data_block_group(bg_config, bg_graph)
    # add_precincts_block_group(bg_config, pr_config, ct_graph, bg_graph)
    # add_election_data(data_config, bg_config, bg_graph)
