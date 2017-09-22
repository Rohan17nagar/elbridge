"""Generate shapefiles for testing."""

import fiona
from shapely.geometry import mapping, box

from utils import cd

def main():
    """Main function."""
    schema = {"geometry": "Polygon", "properties": {"GEOID": "str"}}
    with fiona.open("block-groups/block-groups.shp", 'w', 'ESRI Shapefile',
                    schema=schema) as outfile:
        for i in range(16):
            for j in range(16):
                outfile.write({
                    "geometry": mapping(box(6*i, 6*j, 6*(i+1), 6*(j+1))),
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
                    "geometry": mapping(box(i, j, (i+1), (j+1))),
                    "properties": {
                        "NAME10": "Block {:03d}".format(block_id),
                        "GEOID10": "{:012d}{:03d}".format(block_group_id, block_id)
                    }
                })

if __name__ == '__main__':
    with cd('/var/local/rohan/test_data'):
        main()
