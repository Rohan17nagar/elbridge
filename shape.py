"""
Tools for reading in shapefiles and creating networkx graphs.
"""
import os
import random

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

def _connect_graph(G):
    """Helper function. Connects graph."""
    for n in G.nodes(data=True):
        state = n[1]['block']
        has_connection = False
        
        for o in G.nodes(data=True):
            other = o[1]['block']
            if state is not other and state.touches(other):
                has_connection = True
                border = state.intersection(other)
                assert isinstance(border, (MultiLineString, Point)), \
                    "border ({}, {}) is of type {}".format(n[0], o[0], type(border))
            G.add_edge(n[0], o[0], border=border.length)

        if not has_connection:
            # if this node is marooned, connect it to the closest object
            dist = float('inf')
            closest = None
            
            for node in G.nodes(data=True):
                if node == n:
                    continue
                d = state.centroid.distance(node[1]['block'].centroid)
                
                if d < dist:
                    closest = node
                    dist = d

            G.add_edge(n[0], closest[0], border=0.0)

def create_graph(indir, infile, draw_shapefile=False, draw_graph=False, pickle=False):
    """Using a shapefile at {indir}/{infile}.shp, create a graph.

    Keyword arguments:
    indir -- directory with shapefiles
    infile -- file prefix (i.e., infile="foo" looks for a shapefile called "foo.shp")
    draw_shapefile -- whether to draw the input shapefile (default False)
    draw_graph -- whether to draw the resultant graph (default False)
    pickle -- whether to pickle the resultant graph, stored at indir/infile.pickle (default False)
    """
    G = nx.Graph()
    i = 1
    ignore = set()

    with cd(indir):
        if os.path.isfile("block.txt"):
            # ignore names in file
            with open("block.txt", 'r') as block:
                ignore = set([line.strip() for line in block])

        with fiona.open(infile + ".shp") as blocks:
            for shp in blocks:
                if 'NAME10' in shp['properties']:
                    name = shp['properties']['NAME10']
                elif 'NAME' in shp['properties']:
                    name = shp['properties']['NAME']
                else:
                    name = str(i)

                if name in ignore:
                    continue

                block = shape(shp['geometry'])

                if 'POP10' in shp['properties']:
                    pop = shp['properties']['POP10']
                else:
                    pop = 0

                G.add_node(name, block=block, pop=pop)
                i += 1

    # draw the input shapefile
    if draw_shapefile:
        plot_shapes([n[1]['block'] for n in G.nodes(data=True)])

    _connect_graph(G)

    if draw_graph:
        pos = {n[0] : [n[1]['block'].centroid.x, n[1]['block'].centroid.y]
               for n in G.nodes(data=True)}
        nx.draw_networkx(G, pos=pos)
        plt.show()

    if pickle:
        nx.write_gpickle(G, os.path.join(indir, infile + ".pickle"))

    return G
