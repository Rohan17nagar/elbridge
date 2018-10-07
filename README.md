# Elbridge

Elbridge is a proof-of-concept system that draws Congressional districts with artificial intelligence.

Every decade, after the Census Bureau takes the decennial census, the 43 states with more than one Congressional district have to redraw their district lines to better represent their population. In 37 states, this process, called redistricting, is governed by state legislatures, which generally try and create a partisan advantage for whichever party is in power. The methods by which they do so—and there are many—are generally referred to as "gerrymandering" ([1]).

The goal of this project is straightforward. Humans are bad at drawing district maps. Even when the goal isn't to create a partisan outcome, balancing the dozens of variables and subtleties of population dynamics is a hard problem to solve. Computers are much better at handling the kind of data scale involved in district map creation. Elbridge, in particular, works by drawing millions of potential district maps, studying them, and iterating on them until it creates as good of a map as is possible.

Elbridge was created as part of my honors thesis in computer science.

#### How to run this

Run `python run.py --config=defaults.json`. You'll need to download the appropriate datasets (documentation pending).

This project also comes with a Condorfile to run on the [UT Condor cluster](https://www.cs.utexas.edu/facilities/documentation/condor). To do so, run `condor_submit condor.sub` from a UTCS lab machine.

[1] "Gerry" + "salamander". Elbridge Gerry was the governor of Massachusetts in 1812, and signed into law a district map that was so convoluted that one of its districts looked like a salamander. The term comes from a political cartoon satirizing the map.


## How it works

#### The model

#### The algorithm

Elbridge uses a variant of genetic evolution called memetic evolution, which combines ordinary genetic evolution with periodic gradient descent. Every possible districting of the state is represented by a `|V|`-length array, `C`, such that `C[i] = j` means that vertex `i` is in district `j`. The gene pool is initialized with `p` random chromosomes. From there, the gene pool is sorted via the NSGA-II algorithm, which works as follows:

1. Sort the gene pool into frontiers `F1, F2, ..., Fn`, such that every element of `F1` dominates every element of `F2`, every element of `F2` dominates every element of `F3`, and so on. (A chromosome `X` dominates another chromosome `Y` if, for every score function, `X` is at least as good as `Y`, and for at least one score function, `X` is better than `Y`.)
2. Sort `F1` by determining each candidate's uniqueness, measured by the sum of the distance from it to the next-best and next-worst candidates for every score function.
3. Add all the elements of `F1` to the next generation, until the size of the next generation is equal to `p`.
4. If the next generation has fewer than `p` elements, repeat steps 2 and 3 with `F2`, and so on, until the next generation has `p` elements.
5. Once the next generation of parents is full, perform ordinary selection, crossover, and mutation to get the next generation of children. Restart the algorithm with the gene pool of parents and children.

This algorithm has a number of advantages, but in particular it's fast and more or less guarantees that in addition to fitness, uniqueness is prioritized in choosing the next generation. Uniqueness is important, since a more varied parent population yields a better sample of the search space.

Every 20 generations, Elbridge also optimizes each candidate in the gene pool via simple hill-climbing. Hill-climbing optimizes a candidate by evaluating all of that candidate's neighbors, defined as the candidates created by moving one vertex from its district to a neighboring district, and picking the one with the best overall fitness.