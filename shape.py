# pylint: disable=C0103,R0914
"""
Tools for reading in shapefiles and creating networkx graphs.
"""
import os
import random
from collections import defaultdict

# imports for shapefiles
from shapely.geometry import shape
import fiona
import descartes

# imports for graphs
import networkx as nx
from matplotlib import pyplot as plt
from tqdm import tqdm

# utilities
from utils import cd

def plot_shapes(objects, random_color=False, show_centroids=False, title=""):
    """Plots shapely shapes."""
    fig = plt.figure()
    ax = fig.add_subplot(111)

    # calculate plot bounds
    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')

    # if show_centroids:
    #     areas = [obj.area for obj in objects]
    #     total_area = sum(areas)

    #     x, y = (0, 0)
        
    #     for obj in objects:
    #         x += obj.centroid.x * (float(obj.area) / total_area)
    #         y += obj.centroid.y * (float(obj.area) / total_area)

    for obj in objects:
        color = None
        if isinstance(obj, tuple):
            obj, color = obj

        if not color and random_color:
            color = (random.random(), random.random(), random.random())
            patch = descartes.PolygonPatch(obj, color=color, ec=(0, 0, 0))
        elif color:
            patch = descartes.PolygonPatch(obj, color=color, ec=(0, 0, 0))
        else:
            patch = descartes.PolygonPatch(obj, ec=(0, 0, 0))

        ax.add_patch(patch)

        if show_centroids:
            ax.add_patch(descartes.PolygonPatch(obj.centroid.buffer(0.5)))

        min_x = min(min_x, obj.bounds[0])
        min_y = min(min_y, obj.bounds[1])
        max_x = max(max_x, obj.bounds[2])
        max_y = max(max_y, obj.bounds[3])

    # if show_centroids:
    #     ax.add_patch(descartes.PolygonPatch(Point(x, y).buffer(1.0)))

    ax.set_xlim(min_x - (max_x - min_x) * 0.1, max_x + (max_x - min_x) * 0.1)
    ax.set_ylim(min_y - (max_y - min_y) * 0.1, max_y + (max_y - min_y) * 0.1)

    plt.title(title)

    ax.set_aspect(1)
    plt.show(fig)

def _connect_subgraph(G, a_nodes, b_nodes, same=False):
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
                st_code = shp['properties'].get('ST_CODE')

                precinct_obj = shape(shp['geometry'])

                assert st_code not in precinct_shapes
                precinct_shapes[st_code] = precinct_obj

    return precinct_shapes

def create_county_graph(county_config):
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

    with cd(indir):
        with fiona.open(infile) as counties:
            for shp in tqdm(counties, "Reading counties from shapefile"):
                if shp['properties'].get("STATEFP") != state_code:
                    continue
                shape_obj = shape(shp['geometry'])

                vertex_name = shp['properties'].get("GEOID")

                G.add_node(vertex_name, shape=shape_obj)

    # draw the input shapefile
    if draw_shapefile:
        plot_shapes([n[1]['shape'] for n in G.nodes(data=True)])

    _connect_graph(G)

    if draw_graph:
        pos = {n[0] : [n[1]['shape'].centroid.x, n[1]['shape'].centroid.y]
               for n in G.nodes(data=True)}
        nx.draw_networkx(G, pos=pos)
        plt.show()

    if pickle:
        nx.write_gpickle(G, os.path.join(indir, infile + ".graph.pickle"))

    return G

def create_block_group_graph(block_group_config):
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
        pos = {n[0] : [n[1]['shape'].centroid.x, n[1]['shape'].centroid.y]
               for n in G.nodes(data=True)}
        nx.draw_networkx(G, pos=pos)
        plt.show()

    if pickle:
        nx.write_gpickle(G, os.path.join(indir, infile + ".graph.pickle"))

    return G

def create_block_graph(block_config, block_groups):
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
        pos = {n[0] : [n[1]['shape'].centroid.x, n[1]['shape'].centroid.y]
               for n in G.nodes(data=True)}
        nx.draw_networkx(G, pos=pos)
        plt.show()

    if pickle:
        nx.write_gpickle(G, os.path.join(indir, infile + ".graph.pickle"))

    return G

