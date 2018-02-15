# Shapely + Fiona
You’ll need to install the `shapely` and `fiona` packages via `pip`. See their respective GitHub pages for the exact command, but it’s usually something like `pip install -U shapely`. I recommend doing everything in Python 3, so make sure your `pip` version and `python` version are set accordingly.

Once you have everything set up, you’ll need to navigate to the directory containing all of your shapefiles. This is what my directory looks like:

```
(thesis) rohan@earwig:/var/local/rohan$ cd wa-block-groups/
(thesis) rohan@earwig:/var/local/rohan/wa-block-groups$ ls
total 100M
-rwx------ 1 rohan under    5 Nov 16 21:49 block-groups.cpg*
-rwx------ 1 rohan under 445K Nov 16 21:49 block-groups.dbf*
-rwx------ 1 rohan under  165 Nov 16 21:49 block-groups.prj*
-rwx------ 1 rohan under  25M Nov 16 21:49 block-groups.shp*
-rwx------ 1 rohan under  20K Nov 16 21:49 block-groups.shp.ea.iso.xml*
-rwx------ 1 rohan under  36K Nov 16 21:49 block-groups.shp.iso.xml*
-rwx------ 1 rohan under  21K Nov 16 21:49 block-groups.shp.xml*
-rwx------ 1 rohan under  38K Nov 16 21:49 block-groups.shx*
```

Once you’ve done that, open up a Python REPL:

```
(thesis) rohan@earwig:/var/local/rohan/wa-block-groups$ bpython
bpython version 0.16 on top of Python 3.5.2 /var/local/rohan/thesis/bin/python3
>>>
```

You’ll need to import `fiona` and the `shape`  constructor from Shapely:

```
>>> import fiona
>>> from shapely.geometry import shape
```

Then, you can import all of your shapes:
```
with fiona.open(‘block-groups.shp’) as shapes:
  for shp in shapes:
    print(shp.get('properties'))
    print(shape(shp.get('geometry'))
    # do whatever
```

Each `shp` object is a dictionary, containing a `properties` dictionary and a list of coordinates called `geometry`. You can pass the list into the `shape()` constructor you imported from `shapely.geometry` (like I did above). It’s often useful to annotate the `shape` objects you create with their properties, since `shape()` doesn’t store the object’s properties (name, etc.) in the object it creates.

The `shape` object is super versatile, and supports all kinds of different operations. (See the Shapely manual for a full list.) There are a ton of different unary operators (like `area`, `is_empty`, etc.), and a ton of different binary operators (like `intersects`, `touches`, etc.). Some of the binary operators also return a new object, such as the intersection of two shapes.

A few gotchas:
* Shapely only accepts valid polygons. A valid polygon is one where the coordinates are listed in counterclockwise order in such a way that there’s no self-intersection (in other words, you can’t have empty space inside the polygon—see the docs for a picture). If you have an invalid polygon, an easy fix is this: `shp.buffer(0.0)`. This returns a (valid) polygon that bounds all of the points within a radius of 0.0 units from `shp`—in other words, `shp` itself.
* If you want to see if an object is _entirely contained_ within another object, the correct sequence of predicates is `shp.intersects(other) and not shp.touches(other)`. Don’t ask me why.
* I said it above, but as a reminder: the `shape` constructor does not save property information, which is a lesson I learned the hard way. Save everything first—I used a dictionary of names to shapes.