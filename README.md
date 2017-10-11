# Gerrymandering

## Files

* `shape.py` contains methods that read block group and block shapefiles and convert them to 
graphs.
* `annotater.py` contains methods that annotate block graphs with data, including precinct-level vote breakdowns and block-level demographic data.
* `genetics.py` contains an implementation of NSGA-II, a popular genetic algorithm for multi-objective optimization.
* `objectives.py` contains several objective functions on graphs, used in NSGA-II.
* `disjointset.py` contains a basic implementation of the disjoint-set data structure, used for tracking graph connectivity (the number of connected components in a graph) during graph reconstruction (the process by which a chromosome is converted back into a graph).
* `utils.py` contains several helper functions.
* `test.py` contains several tests of basic functionality.
* `run.py` contains the main runner and configuration file parser.

## How to run this

Run `python run.py --config=defaults.json`. You'll need to download the appropriate datasets (see `data.md` for more information).
