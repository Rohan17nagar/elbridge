"""Testing suite.

Things that need to be tested --
1. Shapefile --> graph (create_block_group_graph)
2. Finer shapefile --> finer graph from coarse graph (create_block_graph)

For these two, generate a shapefile of 100000 2x2 boxes and 400000 1x1 boxes.

"""

import unittest
import os

import shape
from utils import cd

import networkx as nx

class TestShapefileToGraph(unittest.TestCase):
    """Given a coarse and fine shapefile, generate graphs."""
    # @unittest.skipUnless(os.path.exists('block-groups/block-groups.shp'),
    #                      "No block group shapefile found")
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

    # @unittest.skip("No block shapefile yet")
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

        self.assertEqual(len(G2), 96**2)
        self.assertTrue(nx.is_isomorphic(G2, nx.grid_graph([96, 96])))

if __name__ == "__main__":
    with cd('/var/local/rohan/test_data/'):
        unittest.main()
