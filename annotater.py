"""Block graph annotation helpers."""

import csv
import os
import pprint
from collections import defaultdict

import networkx as nx
from tqdm import tqdm
from shapely.geos import TopologicalError

import shape

def _get_precinct_map(graph, bg=False):
    """Get map of precinct code --> blocks in precinct from block graph."""
    precinct_map = defaultdict(list)

    for node, data in graph.nodes(data=True):
        precs = data.get('precincts')
        if precs is None:
            continue

        for prec in precs:
            precinct_map[prec if bg else prec[0]].append(node if bg else (node, prec[1]))

    return precinct_map

def add_election_data(data_config, precinct_config, block_graph):
    # pylint: disable=R0914
    """Add election data from precinct file to graph."""
    indir = data_config.get("directory", "wa-election-data")
    infile = data_config.get("filename", "precinct_results.csv")

    precinct_shapes = shape.get_precinct_shapes(precinct_config)
    precinct_map = _get_precinct_map(block_graph)

    with open(os.path.join(indir, infile)) as data_file:
        records = csv.reader(data_file)
        next(records)

        for record in records:
            [race, county, candidate, precinct, prec_code, votes] = record
            if precinct == "Total" or prec_code == "-1":
                continue

            st_code = county + "{:08}".format(int(prec_code))

            if st_code not in precinct_map and votes != 0:
                raise Exception("Couldn't find precinct", st_code, "in map")

            blocks = precinct_map[st_code]
            assert sum([i for _, i in blocks]) == precinct_shapes[st_code].area, \
                   "precinct area: " + str(precinct_shapes[st_code].area) + ", " + \
                   "block area sum: " + str(sum([i for _, i in blocks]))


def add_precincts_bg(block_group_config, precinct_config, block_group_graph):
    """Match each block group in a graph to the precinct that contains it."""
    indir = block_group_config.get("directory", "wa-block-groups")
    infile = block_group_config.get("filename", "block-groups.shp")

    pickle = block_group_config.get("pickle_graph", True)

    if any(['precincts' in data for _, data in block_group_graph.nodes(data=True)]):
        return

    # map block group to precincts it intersects with
    block_group_map = defaultdict(list)

    precinct_shapes = shape.get_precinct_shapes(precinct_config)


    for st_code, precinct_obj in tqdm(precinct_shapes.items(),
                                      "Assigning block groups to precincts"):
        found = False

        for block_group_node, block_group_data in block_group_graph.nodes(data=True):
            block_group_obj = block_group_data.get('shape')
            if precinct_obj.intersects(block_group_obj) \
                    and not precinct_obj.touches(block_group_obj):
                block_group_map[block_group_node].append(st_code)
                found = True

        assert found

    nx.set_node_attributes(block_group_graph, 'precincts',
                           {block_group: value for block_group, value
                            in block_group_map.items()})
    if pickle:
        nx.write_gpickle(block_group_graph, os.path.join(indir, infile + ".annotated_graph.pickle"))

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
        precincts_over_block_group = block_group_graph.node[block_group_name].get('precincts', [])

        block_obj = block_data['shape']
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

    nx.set_node_attributes(block_graph, 'precincts',
                           {block: value for block, value in block_map.items()})

    if pickle:
        nx.write_gpickle(block_graph, os.path.join(indir, infile + ".annotated_graph.pickle"))

    print("Found", count, "invalid or null blocks.")

def test(precinct_config, block_graph, block_group_graph):
    """Test!"""
    precinct_shapes = shape.get_precinct_shapes(precinct_config)

    precinct_map = _get_precinct_map(block_group_graph, bg=True)

    missing_bg = set(precinct_shapes.keys()) - set(precinct_map.keys())
    print("precincts not in block group graph:", len(missing_bg))

    for prec_code in missing_bg:
        print(prec_code)
        precinct_obj = precinct_shapes[prec_code]
        blocks = [data for _, data in block_group_graph.nodes(data=True)]
        closest_blocks = sorted(blocks,
                                key=lambda x, t=precinct_obj:
                                t.centroid.distance(x.get('shape').centroid))[:50]

        for obj in closest_blocks:
            print(precinct_obj.intersects(obj.get('shape')) and not \
                  precinct_obj.touches(obj.get('shape')),
                  obj.get('precincts'))

    precinct_map = _get_precinct_map(block_graph)

    missing_b = set(precinct_shapes.keys()) - set(precinct_map.keys())
    print("precincts not in block graph:", len(missing_b))

    for prec_code in missing_b:
        print(prec_code)
        precinct_obj = precinct_shapes[prec_code]
        closest_blocks = sorted(block_graph.nodes(data=True),
                                key=lambda x, t=precinct_obj:
                                t.centroid.distance(x[1].get('shape').centroid))[:50]

        for name, obj in closest_blocks:
            print(name,
                  precinct_obj.intersects(obj.get('shape')) and not \
                  precinct_obj.touches(obj.get('shape')),
                  precinct_obj.buffer(0).intersection(obj.get('shape')).area,
                  obj.get('precincts'),
                  prec_code in block_group_graph.node[name[:-3]].get('precincts', []))
        shape.plot_shapes([(obj.get('shape'), (1, 0, 0)
                            if precinct_obj.intersects(obj.get('shape')) \
                                and not precinct_obj.touches(obj.get('shape')) else (0, 0, 1))
                           for _, obj in closest_blocks] + [(precinct_obj, (0, 0, 0, 0))])
