#!/bin/bash
echo $(ls -l /scratch/cluster/rohan)
echo $(pwd)
python3 -m kernprof -o run.py.output.lprof -l run.py 
if [[ ! -d output ]]; then
  mkdir output
fi

mv *.output.* output
