import networkx as nx

from elbridge.readers import shape, annotater
from elbridge.runners import evaluation
from elbridge.utilities.utils import cd


def create_graphs(data_dir, configs, districts):
    with cd(data_dir):
        county_graph = shape.create_county_graph(configs.get('county'))
        annotater.initialize_county_graph(
            configs.get('county'), configs.get('precinct'), configs.get('voting_data'), county_graph
        )

        block_group_graph = shape.create_block_group_graph(configs.get('block_group'))
        annotater.initialize_block_group_graph(
            configs.get('block_group'), configs.get('precinct'), configs.get('voting_data'),
            county_graph, block_group_graph
        )

        print("Finished reading in all graphs. Leaving data directory.")

    county_graph['graph']['districts'] = block_group_graph['graph']['districts'] = districts

    return nx.freeze(county_graph), nx.freeze(block_group_graph)


def evaluate(data_dir, configs, districts, reload_only):
    """Main function."""
    county_graph, block_group_graph = create_graphs(data_dir, configs, districts)

    if reload_only:
        return

    best_solutions = evaluation.evaluate_graph(
        block_group_graph, "Block Group Graph", "bgg", config=configs.get('params')
    )

    print("Finished evolution.")

    final = best_solutions[0]
    final.plot(save=True)
