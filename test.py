"""Testing."""

import requests
from shapely.geometry import shape, Point, MultiPolygon, Polygon
from descartes import PolygonPatch
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
import fiona
from tqdm import tqdm

blocks = []

def _load_blocks():
    # point = Point(48.0817047, -123.1080016)
    with fiona.open("/var/local/rohan/wa-blocks/blocks.shp") as blks:
        for blk in tqdm(blks):
            block = shape(blk['geometry'])

            blocks.append(block)


def test():
    """Testing code."""
    test_string = "308 SPRUCE ST W SEQUIM WA 98382"

    r = requests.get("https://maps.googleapis.com/maps/api/geocode/json",
                     params={"address": test_string,
                             "key": "AIzaSyDV3WKAIL3ywBs7yMafnZiDi4qV3nAS4tI"})
    output = r.json()['results']

    coords = output[0]['geometry']['location']
    point = Point(coords['lng'], coords['lat'])

    print(point)

    for block in tqdm(blocks):
        if block.intersects(point):
            block.color = "#0000FF"
            print("FOUND!")
        else:
            block.color = "#FF0000"

    fig = plt.figure()
    ax = fig.add_subplot(111)

    mp = MultiPolygon(blocks)
    minx, miny, maxx, maxy = mp.bounds
    w, h = maxx - minx, maxy - miny

    ax.set_xlim(minx - 0.2 * w, maxx + 0.2 * w)
    ax.set_ylim(miny - 0.2 * h, maxy + 0.2 * h)
    ax.set_aspect(1)

    patches = []
    for idx, p in enumerate(blocks):
        patches.append(PolygonPatch(p, fc=p.color, ec='#555555', alpha=1.))
    ax.add_collection(PatchCollection(patches, match_original=True))

    ax.add_patch(PolygonPatch(point.buffer(0.001)))
    
    ax.set_aspect(1)
    plt.show(fig)


if __name__ == "__main__":
    _load_blocks()
    test()
