#!/bin/bash

cd ~/src/thesis
if [[ ! -d out ]]; then
  mkdir out
fi
echo $(whoami)
echo $(ls -l /scratch/cluster/rohan)
echo $(ls -l .)
echo $(ls -l ..)
python3 -m kernprof -o out/run.py.lprof -l run.py

echo $(ls -l .)
