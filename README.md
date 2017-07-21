# Gerrymandering

### How to run this

Pull this repo:

```git clone git@github.com:rohan/gerrymander.git
cd gerrymander/```

Now, you'll need to create a data directory for your shapefiles. In this example, we'll use the Census Bureau's shapefiles for the 50 states. (You can download it at [the Census Bureau website](https://www.census.gov/cgi-bin/geo/shapefiles/index.php?year=2016&layergroup=States+%28and+equivalent%29).) Download and unzip into a folder called `data/state_shapes`, then rename all of the files to `state_shapes.xxx` (where `xxx` is the file extension, for example `state_shapes.shp`).

To run, execute `python run.py`. This takes a bunch of command-line arguments.

`python run.py --log=WARN --reload --data=data --dir=state_shapes --samples=100 --steps=100`

Each of these modifies a different flag.

* `--log` sets the logging level. The default is `WARN`.
* `--reload` force-reconstructs a graph from the shapefiles. Normally, once the graph is built, it's pickled (and stored at `data_dir/file_dir/file_dir.pickle`, in our example `data/state_shapes/state_shapes.pickle`). However, if you want to reconstruct the graph for debugging reasons, use this flag.
* `--data` sets the data directory (by default `data/`). In this directory, you'll have a bunch of folders with shapefiles/other datasets inside.
* `--dir` sets the dataset directory (by default `state_shapes/`). Note that all files inside `data_dir/file_dir` have to be called `file_dir.xxx`; in our example, all the files have to be called `state_shapes.xxx`.
* `--samples` sets the number of starting positions for hill-climbing. The higher this is, the more likely you'll find the global maximum, but the longer execution will take. (NB: on my MacBook, which has a 1.2 GHz Core M processor, each iteration takes around 5 seconds.)
* `--steps` sets the maximum number of steps that can be taken from one starting position. In practice, this upper limit is rarely reached.

## The code

This codebase converts raw shapefile data and associated population/demographic data into a graph, runs a heuristic-based graph partitioning algorithm on that graph, and returns the best partition that satisfies a number of score functions.

### Converting a raw shapefile to a graph