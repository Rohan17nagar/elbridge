#!/bin/bash
echo $(ls -l)
source thesis/bin/activate
thesis/bin/kernprof -l run.py
