#!/bin/sh
python3 setup.py build_ext --inplace
python3 solver.py --turns=12 --straight=4 --ups=2 --downs=2 --pillars=4
rm paths.pickle
