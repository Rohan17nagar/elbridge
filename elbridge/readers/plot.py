import os
import random

import descartes
import matplotlib.pyplot as plt
import networkx as nx


def plot_graph(graph):
    """Plots a block graph."""
    nx.draw_networkx(graph, pos={node: list(data.get('shape').centroid.coords)[0]
                                 for node, data in graph.nodes(data=True)})
    plt.show()


def plot_shapes(objects, random_color=False, title="plot", save=False):
    """Plots shapely shapes."""
    fig = plt.figure()
    ax = fig.add_subplot(111)

    # calculate plot bounds
    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')

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
    if save:
        plt.savefig('out/{}.png'.format(title))

        os.chmod('out/{}.png'.format(title), 0o666)
    else:
        plt.show(fig)

    plt.cla()
