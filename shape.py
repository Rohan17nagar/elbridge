# pylint: disable=C0103
"""
Tools for reading in shapefiles and creating networkx graphs.
"""
import os
import random
from collections import defaultdict

# imports for shapefiles
from shapely.geometry import shape, Point, MultiLineString
import fiona
import descartes

# imports for graphs
import networkx as nx
from matplotlib import pyplot as plt

# utilities
from utils import cd

def plot_shapes(objects, random_color=False, show_centroids=False):
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
        if random_color:
            color = (random.random(), random.random(), random.random())
            patch = descartes.PolygonPatch(obj, color=color)
        else:
            patch = descartes.PolygonPatch(obj)

        ax.add_patch(patch)

        if show_centroids:
            ax.add_patch(descartes.PolygonPatch(obj.centroid.buffer(0.5)))

        min_x = min(min_x, obj.bounds[0])
        min_y = min(min_y, obj.bounds[1])
        max_x = max(max_x, obj.bounds[2])
        max_y = max(max_y, obj.bounds[3])

    # if show_centroids:
    #     ax.add_patch(descartes.PolygonPatch(Point(x, y).buffer(1.0)))

    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)

    ax.set_aspect(1)
    plt.show(fig)

def _connect_subgraph(G, a_nodes, b_nodes):
    """Helper function. Connects graph."""
    i = 0

    # G must contain all nodes in a_nodes and b_nodes
    assert all([G.has_node(node) for node, _ in a_nodes + b_nodes])

    same = False
    if a_nodes == b_nodes:
        same = True

    while i < len(a_nodes):
        n, n_data = a_nodes[i]
        this = n_data['shape']
        has_connection = False
        
        # if a_nodes == b_nodes, don't need to compare anything in b_nodes[:i] to a_nodes[i]
        for o, o_data in b_nodes[i:] if same else b_nodes:
            other = o_data['shape']
            if this is not other and this.touches(other):
                has_connection = True
                border = this.intersection(other)
                assert isinstance(border, (MultiLineString, Point)), \
                    "border ({}, {}) is of type {}".format(n, o, type(border))
            G.add_edge(n, o, border=border.length)

        if not has_connection:
            # if this node is marooned, connect it to the closest object
            dist = float('inf')
            closest = None
            
            for node, data in G.nodes(data=True):
                if node == n:
                    continue
                d = this.centroid.distance(data['shape'].centroid)
                
                if d < dist:
                    closest = node
                    dist = d

            G.add_edge(n, closest, border=0.0)

def _connect_graph(G):
    _connect_subgraph(G, G.nodes(data=True), G.nodes(data=True))


def create_county_graph(county_config):
    """Build a county graph."""

    state_code = county_config.get("state_code", 53)
    
    indir = county_config.get("directory", "wa-counties")
    infile = county_config.get("filename", "wa-counties.shp")
    
    draw_shapefile = county_config.get("draw_shapefile", False)
    draw_graph = county_config.get("draw_graph", False)

    pickle = county_config.get("pickle_graph", True)

    reload_graph = county_config.get("reload_graph", False)

    if not reload_graph and os.path.exists(os.path.join(indir, infile + ".graph.pickle")):
        return nx.read_gpickle(os.path.join(indir, infile + ".graph.pickle"))

    G = nx.Graph()

    with cd(indir):
        with fiona.open(infile) as counties:
            for idx, shp in enumerate(counties):
                if "STATEFP" not in shp['properties'] \
                    or shp['properties']["STATEFP"] is not str(state_code):
                    # ignore counties not in the desired state
                    continue

                shape_obj = shape(shp['geometry'])

                vertex_name = shp['properties'].get("COUNTYFP", idx)

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

# pylint: disable=R0914
def create_block_graph(block_config, counties):
    """Using a county graph as a base, build a block graph."""

    indir = block_config.get("directory", "wa-blocks")
    infile = block_config.get("filename", "wa-blocks.shp")
    
    draw_shapefile = block_config.get("draw_shapefile", False)
    draw_graph = block_config.get("draw_graph", False)

    pickle = block_config.get("pickle_graph", True)

    reload_graph = block_config.get("reload_graph", False)

    if not reload_graph and os.path.exists(os.path.join(indir, infile + ".graph.pickle")):
        return nx.read_gpickle(os.path.join(indir, infile + ".graph.pickle"))

    # county --> graph of vertices in that county
    county_graphs = defaultdict(nx.Graph)

    with cd(indir):
        with fiona.open(infile + ".shp") as blocks:
            for idx, shp in enumerate(blocks):
                county_code = shp['properties'].get('COUNTYFP10', -1)
                name = shp['properties'].get('NAME10', "Block " + idx)
                block = shape(shp['geometry'])
                county_graphs[county_code].add_node(name, shape=block)

    G = nx.Graph()

    for graph in county_graphs.values():
        G = nx.compose(G, graph)

    if draw_shapefile:
        plot_shapes([n[1]['shape'] for n in G.nodes(data=True)])

    for i in counties.nodes():
        _connect_subgraph(G, county_graphs[i].nodes(data=True), county_graphs[i].nodes(data=True))

    for i, j in counties.edges():
        _connect_subgraph(G, county_graphs[i].nodes(data=True), county_graphs[j].nodes(data=True))

    if draw_graph:
        pos = {n[0] : [n[1]['shape'].centroid.x, n[1]['shape'].centroid.y]
               for n in G.nodes(data=True)}
        nx.draw_networkx(G, pos=pos)
        plt.show()

    if pickle:
        nx.write_gpickle(G, os.path.join(indir, infile + ".graph.pickle"))

    return G

