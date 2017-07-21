"""
Tools for reading in shapefiles and creating networkx graphs.
"""
# imports for shapefiles
from shapely.geometry import shape, Point, MultiLineString
from shapely.affinity import translate
from shapely.ops import cascaded_union
import fiona
import descartes

import random

# imports for graphs
import networkx as nx
from matplotlib import pyplot as plt

# utilities
from utils import cd
import pprint
import os

# Plots a collection of shapefiles.
def plot_objects(objects, random_color=False, centroids=False, explode=False):
  fig = plt.figure()
  ax = fig.add_subplot(111)

  min_x = float('inf')
  min_y = float('inf')
  max_x = float('-inf')
  max_y = float('-inf')

  if centroids:
    centroids = []
    areas = []

    for obj in objects:
      print(obj.centroid)
      centroids.append(obj.centroid)
      areas.append(obj.area)

    x, y = (0, 0)
    for i in range(len(centroids)):
      x += centroids[i].x * (float(areas[i]) / sum(areas))
      y += centroids[i].y * (float(areas[i]) / sum(areas))

  if centroids and explode:
    objs = map(lambda obj: translate(obj, xoff=(obj.centroid.x - x)*0.1, yoff=(obj.centroid.y - y) * 0.1), objects)
  else:
    objs = objects

  for obj in objs:
    color = (random.random(), random.random(), random.random())
    if random_color:
      patch = descartes.PolygonPatch(obj, color=color)
    else:
      patch = descartes.PolygonPatch(obj)

    ax.add_patch(patch)

    if centroids:
      if random_color:
        ax.add_patch(descartes.PolygonPatch(obj.centroid.buffer(0.5)))
      else:
        ax.add_patch(descartes.PolygonPatch(obj.centroid.buffer(0.5)))

    minx, miny, maxx, maxy = obj.bounds
    min_x = min(min_x, minx)
    min_y = min(min_y, miny)
    max_x = max(max_x, maxx)
    max_y = max(max_y, maxy)

  if centroids:
    ax.add_patch(descartes.PolygonPatch(Point(x,y).buffer(1.0)))

  ax.set_xlim(min_x, max_x)
  ax.set_ylim(min_y, max_y)
  ax.set_aspect(1)
  plt.show(fig)

# Converts a shapefile located at indir/infile.shp to a networkx graph.
# If draw_graph is set to True, the graph is drawn using matplotlib.
def create_graph(indir, infile, draw_shapefile=False, draw_graph=False, pickle=False):
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

  if draw_shapefile:
    plot_objects([n[1]['block'] for n in G.nodes(data=True)])

  for n in G.nodes(data=True):
    state = n[1]['block']
    has_connection = False
    for o in G.nodes(data=True):
      other = o[1]['block']
      if state is not other and state.touches(other):
        has_connection = True
        border = state.intersection(other)
        assert isinstance(border, MultiLineString) or isinstance(border, Point), \
          "border ({}, {}) is of type {}".format(n[0], o[0], type(border))
        G.add_edge(n[0], o[0], border=border.length)

    if not has_connection:
      # connect it to the closest object
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

  if draw_graph:
    pos = { n[0] : [n[1]['block'].centroid.x, n[1]['block'].centroid.y] for n in G.nodes(data=True) }
    nx.draw_networkx(G, pos=pos)
    plt.show()

  if pickle:
    nx.write_gpickle(G, os.path.join(indir, infile + ".pickle"))

  return G
