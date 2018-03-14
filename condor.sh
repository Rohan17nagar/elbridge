#!/bin/bash

cd ~/src/thesis
if [[ ! -d out ]]; then
  mkdir out
fi

python3 -m kernprof -o out/run.py.lprof -l run.py