# pylint: disable=C0103, R0903
"""Testing suite.

Things that need to be tested --
1. Shapefile --> graph (create_block_group_graph)
2. Finer shapefile --> finer graph from coarse graph (create_block_graph)

For these two, generate a shapefile of 100000 2x2 boxes and 400000 1x1 boxes.

"""

import os
import unittest

import fiona
import networkx as nx
from shapely.geometry import mapping, box

from elbridge.readers import shape
from elbridge.utilities.utils import cd


def generate_test_data():
    """Generate shapefiles for testing."""
    schema = {"geometry": "Polygon", "properties": {"GEOID": "str"}}
    with fiona.open("block-groups/block-groups.shp", 'w', 'ESRI Shapefile',
                    schema=schema) as outfile:
        for i in range(16):
            for j in range(16):
                outfile.write({
                    "geometry": mapping(box(6 * i, 6 * j, 6 * (i + 1), 6 * (j + 1))),
                    "properties": {
                        "GEOID": "{:012d}".format(16 * i + j)
                    }
                })

    schema = {"geometry": "Polygon", "properties": {"NAME10": "str", "GEOID10": "str"}}
    with fiona.open("blocks/blocks.shp", 'w', 'ESRI Shapefile', schema=schema) as outfile:
        for i in range(96):
            for j in range(96):
                block_group_id = (i // 6) * 16 + (j // 6) * 1
                block_id = (i % 6) * 6 + (j % 6) * 1
                outfile.write({
                    "geometry": mapping(box(i, j, (i + 1), (j + 1))),
                    "properties": {
                        "NAME10": "Block {:03d}".format(block_id),
                        "GEOID10": "{:012d}{:03d}".format(block_group_id, block_id)
                    }
                })


class TestShapefileToGraph(unittest.TestCase):
    """Given a coarse and fine shapefile, generate graphs."""

    def test_block_group_graph(self):
        """Test that block group graph generates correctly."""
        block_group_config = {
            "directory": "block-groups",
            "filename": "block-groups.shp",
            "pickle_graph": False,
            "draw_graph": False,
            "draw_shapefile": False,
            "reload_graph": False
        }

        G = shape.create_block_group_graph(block_group_config)

        self.assertEqual(len(G), 256)
        print(G.edges("000000000000", data=True))
        self.assertTrue(nx.is_isomorphic(G, nx.grid_graph([16, 16])))

        expected_nodes = ["{:012d}".format(i) for i in range(256)]

        self.assertEqual(set(expected_nodes), set(G.nodes()))

        self.assertFalse(os.path.exists("block-groups/block-groups.graph.pickle"))

    def test_block_graph(self):
        """Test that block graph generates correctly."""
        block_group_config = {
            "directory": "block-groups",
            "filename": "block-groups.shp",
            "pickle_graph": False,
            "draw_graph": False,
            "draw_shapefile": False,
            "reload_graph": False
        }

        G = shape.create_block_group_graph(block_group_config)

        block_config = {
            "directory": "blocks",
            "filename": "blocks.shp",
            "pickle_graph": False,
            "draw_graph": False,
            "draw_shapefile": False,
            "reload_graph": False
        }

        G2 = shape.create_block_graph(block_config, G)

        self.assertEqual(len(G2), 96 ** 2)
        self.assertTrue(nx.is_isomorphic(G2, nx.grid_graph([96, 96])))


if __name__ == "__main__":
    with cd('/var/local/rohan/test_data/'):
        if not os.path.exists('block-groups/block-groups.shp') \
                or not os.path.exists('blocks/blocks.shp'):
            generate_test_data()
        unittest.main()
