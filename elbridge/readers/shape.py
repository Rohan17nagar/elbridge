# pylint: disable=C0103,R0914
"""
Tools for reading in shapefiles and creating networkx graphs.
"""
import os
from collections import defaultdict

# imports for shapefiles
from typing import List

from shapely.geometry import shape
import fiona

# imports for graphs
import networkx as nx
from matplotlib import pyplot as plt
from tqdm import tqdm

# utilities
from elbridge.readers.plot import plot_shapes
from elbridge.utils import cd


def _connect_subgraph(G: nx.Graph, a_nodes: List[int], b_nodes: List[int], same=False):
    """Helper function. Connects graph."""

    # G must contain all nodes in a_nodes and b_nodes
    assert all([G.has_node(node) for node in a_nodes + b_nodes])

    for idx in tqdm(range(len(a_nodes)), "Discovering edges"):
        n_name = a_nodes[idx]
        n_data = G.nodes()[n_name]
        this = n_data.get('shape')
        has_connection = False

        # if a_nodes == b_nodes, don't need to compare anything in b_nodes[:i] to a_nodes[i]
        for o_name in b_nodes[idx:] if same else b_nodes:
            o_data = G.nodes()[o_name]
            other = o_data.get('shape')
            if this is not other and this.touches(other):
                has_connection = True
                border = this.intersection(other)
                if border.length == 0.0:
                    continue

                G.add_edge(n_name, o_name, border=border.length)

        if same and not has_connection:
            # if this node is marooned, connect it to the closest object
            sequence = [node for node in a_nodes if node != n_name]
            if not sequence:
                continue
            closest = min([node for node in a_nodes if node != n_name],
                          key=lambda o_name, t=this:
                          t.centroid.distance(G.nodes()[o_name]['shape'].centroid))

            G.add_edge(n_name, closest, border=0.0)


def _connect_graph(G):
    _connect_subgraph(G, list(G.nodes()), list(G.nodes()), same=True)


def get_precinct_shapes(precinct_config):
    """Get precincts from file."""
    indir = precinct_config.get("directory", "wa-precincts")
    infile = precinct_config.get("filename", "precincts.shp")

    precinct_shapes = {}

    with cd(indir):
        with fiona.open(infile) as precincts:
            for shp in tqdm(precincts, "Reading precincts from shapefile"):
                precinct_obj = shape(shp['geometry'])
                precinct_data = shp['properties']

                if not precinct_obj.is_valid:
                    plot_shapes([precinct_obj])
                    assert False
                assert precinct_obj.area != 0, precinct_obj.area

                st_code = precinct_data.get('ST_CODE')

                assert st_code not in precinct_shapes
                precinct_shapes[st_code] = (precinct_obj, precinct_data)

    return precinct_shapes


def create_county_graph(county_config) -> nx.Graph:
    """Build a county graph."""

    indir = county_config.get("directory", "wa-counties")
    infile = county_config.get("filename", "counties.shp")

    draw_shapefile = county_config.get("draw_shapefile", False)
    draw_graph = county_config.get("draw_graph", False)

    pickle = county_config.get("pickle_graph", True)

    reload_graph = county_config.get("reload_graph", False)

    state_code = county_config.get("state_code", "53")

    if not reload_graph:
        if os.path.exists(os.path.join(indir, infile + ".annotated_graph.pickle")):
            return nx.read_gpickle(os.path.join(indir, infile + ".annotated_graph.pickle"))
        elif os.path.exists(os.path.join(indir, infile + ".graph.pickle")):
            return nx.read_gpickle(os.path.join(indir, infile + ".graph.pickle"))

    G = nx.Graph()
    # map English name (e.g., King County) to GEOID (e.g., 53033)
    name_to_geoid = {}

    with cd(indir):
        with fiona.open(infile) as counties:
            for shp in tqdm(counties, "Reading counties from shapefile"):
                if shp['properties'].get("STATEFP") != state_code:
                    continue
                shape_obj = shape(shp['geometry'])

                # the vertex in the graph is named for the geoid
                # the county name is also stored for data matching
                vertex_name = shp['properties'].get("GEOID")
                county_name = shp['properties'].get("NAME")

                G.add_node(vertex_name, shape=shape_obj)
                name_to_geoid[county_name] = vertex_name

    # draw the input shapefile
    if draw_shapefile:
        plot_shapes([n[1]['shape'] for n in G.nodes(data=True)])

    _connect_graph(G)

    if draw_graph:
        pos = {n[0]: [n[1]['shape'].centroid.x, n[1]['shape'].centroid.y] for n in G.nodes(data=True)}
        nx.draw_networkx(G, pos=pos)
        plt.show()

    G.graph['name_map'] = name_to_geoid

    if pickle:
        nx.write_gpickle(G, os.path.join(indir, infile + ".graph.pickle"))

    return G


def create_block_group_graph(block_group_config) -> nx.Graph:
    """Build a block group graph."""

    indir = block_group_config.get("directory", "wa-block-groups")
    infile = block_group_config.get("filename", "block-groups.shp")

    draw_shapefile = block_group_config.get("draw_shapefile", False)
    draw_graph = block_group_config.get("draw_graph", False)

    pickle = block_group_config.get("pickle_graph", True)

    reload_graph = block_group_config.get("reload_graph", False)

    if not reload_graph:
        if os.path.exists(os.path.join(indir, infile + ".annotated_graph.pickle")):
            return nx.read_gpickle(os.path.join(indir, infile + ".annotated_graph.pickle"))
        elif os.path.exists(os.path.join(indir, infile + ".graph.pickle")):
            return nx.read_gpickle(os.path.join(indir, infile + ".graph.pickle"))

    G = nx.Graph()

    with cd(indir):
        with fiona.open(infile) as block_groups:
            for shp in tqdm(block_groups, "Reading block groups from shapefile"):
                shape_obj = shape(shp['geometry'])

                vertex_name = shp['properties'].get("GEOID")

                G.add_node(vertex_name, shape=shape_obj)

    # draw the input shapefile
    if draw_shapefile:
        plot_shapes([n[1]['shape'] for n in G.nodes(data=True)])

    _connect_graph(G)

    if draw_graph:
        pos = {n[0]: [n[1]['shape'].centroid.x, n[1]['shape'].centroid.y] for n in G.nodes(data=True)}
        nx.draw_networkx(G, pos=pos)
        plt.show()

    if pickle:
        nx.write_gpickle(G, os.path.join(indir, infile + ".graph.pickle"))

    return G


def create_block_graph(block_config, block_groups: nx.Graph) -> nx.Graph:
    """Using a block group graph as a base, build a block graph."""

    indir = block_config.get("directory", "wa-blocks")
    infile = block_config.get("filename", "blocks.shp")

    draw_shapefile = block_config.get("draw_shapefile", False)
    draw_graph = block_config.get("draw_graph", False)

    pickle = block_config.get("pickle_graph", True)

    reload_graph = block_config.get("reload_graph", False)

    if not reload_graph:
        if os.path.exists(os.path.join(indir, infile + ".annotated_graph.pickle")):
            return nx.read_gpickle(os.path.join(indir, infile + ".annotated_graph.pickle"))
        elif os.path.exists(os.path.join(indir, infile + ".graph.pickle")):
            return nx.read_gpickle(os.path.join(indir, infile + ".graph.pickle"))

    G = nx.Graph()
    # block group --> list of vertices in that block group
    blocks_per_block_group = defaultdict(list)

    with cd(indir):
        with fiona.open(infile) as blocks:
            for shp in tqdm(blocks, "Reading blocks from shapefile"):
                geo_id = shp['properties'].get('GEOID10')
                # name = shp['properties'].get('NAME10', "Block " + str(idx))
                block_obj = shape(shp['geometry'])
                G.add_node(geo_id, shape=block_obj)

                # GEOID of block == GEOID of block group + block ID
                block_group = geo_id[:-3]
                blocks_per_block_group[block_group].append(geo_id)

    if draw_shapefile:
        plot_shapes([n[1]['shape'] for n in G.nodes(data=True)])

    for i in tqdm(block_groups.nodes(), "Building block group subgraphs"):
        _connect_subgraph(G, blocks_per_block_group[i], blocks_per_block_group[i], same=True)

    for i, j in tqdm(block_groups.edges(), "Building cross-block group subgraphs"):
        _connect_subgraph(G, blocks_per_block_group[i], blocks_per_block_group[j])

    if draw_graph:
        pos = {n[0]: [n[1]['shape'].centroid.x, n[1]['shape'].centroid.y] for n in G.nodes(data=True)}
        nx.draw_networkx(G, pos=pos)
        plt.show()

    if pickle:
        nx.write_gpickle(G, os.path.join(indir, infile + ".graph.pickle"))

    return G
