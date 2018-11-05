import os
import matplotlib as mpl
if os.environ.get('DISPLAY', '') == '':
    print('Using non-interactive Agg backend.')
    mpl.use('Agg')

import random

import descartes
import matplotlib.pyplot as plt
import networkx as nx

from elbridge.utilities.utils import cd


def plot_shape_graph(graph):
    """Plots a block graph."""
    nx.draw_networkx(graph, pos={
        node: list(data.get('shape').centroid.coords)[0] for node, data in graph.nodes(data=True)
    })

    plt.show()


def plot_graph(chromosome):
    master_graph = chromosome.get_master_graph()
    graph = nx.Graph(master_graph)

    for i, j in master_graph.edges():
        if not chromosome.in_same_component(i, j):
            graph.remove_edge(i, j)

    nx.draw_networkx(
        graph, pos={v: v for v in graph}, labels={v: "{} {}".format(v, chromosome.get_component(v)) for v in graph}
    )

    plt.title(chromosome.score_format())
    plt.show()


def plot_shapes(objects, outdir="out/", random_color=False, title="plot"):
    """Plots shapely shapes."""
    fig = plt.figure()
    ax = fig.add_subplot(111)

    # calculate plot bounds
    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')

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

        min_x = min(min_x, obj.bounds[0])
        min_y = min(min_y, obj.bounds[1])
        max_x = max(max_x, obj.bounds[2])
        max_y = max(max_y, obj.bounds[3])

    ax.set_xlim(min_x - (max_x - min_x) * 0.1, max_x + (max_x - min_x) * 0.1)
    ax.set_ylim(min_y - (max_y - min_y) * 0.1, max_y + (max_y - min_y) * 0.1)

    plt.title(title)

    ax.set_aspect(1)

    if outdir:
        with cd(outdir):
            plt.savefig('plot.png')
            os.chmod('plot.png', 0o666)
    else:
        plt.show()
