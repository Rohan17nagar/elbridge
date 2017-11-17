## The Algorithm

Genetic algorithms are generally divided into three components that model real-world evolution. In the beginning, there are P individuals in the gene pool (usually randomly generated). Selection, the first component, randomly picks two parent individuals from which to create children. This typically happens semirandomly, where the probability of a candidate being chosen is proportional to its fitness. Crossover, the second component, is the process by which two parent candidates are divided and recombined to form children candidates. Mutation, the third component, is the process by which a child candidate undergoes random change (for example, having a bit flipped). In this work, we add a fourth step, local search, which takes a child candidate and finds the closest local maximum. (This form of augmented GA is called hybrid, or memetic, GA.)

First is the question of how candidates are represented. In this work, where candidates are partitions of a graph, there are several options. The simplest, and the one frequently used by other GAs for graph partitioning, uses a |V|-length array of integers A, where A[i] is the number of the connected component vertex i is in. For example, a 3-partition of a graph with six vertices, 0 through 5, where vertices i and i + 3 are in the same partition, is represented as 012012. This approach has the advantage of simplicity, but suffers from two drawbacks. First, partition numbering from parent to child is nontrivial to standardize (a process called normalization), such that one parent's idea of what partition 1 represents might be different from the other parent's. Further, since vertices and not edges are represented, it's relatively difficult to go from representation to graph. Although neither of these problems are insurmountable, it's still worth considering a different approach.

Here, we use a different encoding. A chromosome is an |E|-length array A, where A[i] is the priority of edge i. Edges are removed from the starting graph G in order of their priority until G is partitioned into k connected components. This approach has the advantage of maintaining some of the richness of the graph structure without compromising on simplicity.

Selection...

Crossover is straightforward, and works by 