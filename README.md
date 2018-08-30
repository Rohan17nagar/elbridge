# Gerrymandering

## Files

* `shape.py` contains methods that read block group and block shapefiles and convert them to 
graphs.
* `annotater.py` contains methods that annotate block graphs with data, including precinct-level vote breakdowns and block-level demographic data.
* `genetics.py` contains an implementation of NSGA-II, a popular genetic algorithm for multi-objective optimization.
* `objectives.py` contains several objective functions on graphs, used in NSGA-II.
* `disjoint_set.py` contains a basic implementation of the disjoint-set data structure, used for tracking graph connectivity (the number of connected components in a graph) during graph reconstruction (the process by which a chromosome is converted back into a graph).
* `utils.py` contains several helper functions.
* `test_shape.py` contains several tests of basic functionality.
* `run.py` contains the main runner and configuration file parser.

## How to run this

Run `python run.py --config=defaults.json`. You'll need to download the appropriate datasets (see `data.md` for more information).

To run on condor, run `condor_submit condor.sub`.

## Open Questions

* Why does the algorithm always plateau at 0?
  * This means that the smallest district has population 0. Maybe ignore any block group of size 0? These can then be retrofitted back into the output, or ignored entirely.
  * It could also mean that the minimum-size heuristic isn't a very good one.