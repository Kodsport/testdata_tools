#!/usr/bin/env bash
USE_SCORING=0
. ../../testdata_tools/gen.sh

# Example test data generator for non-scoring problems.

# For unlimited stack:
# ulimit -s unlimited

# Choose your solution
use_solution js.cpp

# Compile generators
compile gen_random.py # Arguments: length seed

# Generate answers to sample cases (optional)
sample 1
sample 2
sample 3

# Note: tc automatically adds a deterministic, pseudo-random seed argument to your generator
tc exact random 10
tc one_off_01 random 11
tc one_off_02 random 11
tc one_off_03 random 11
tc_manual ../manual-tests/1.in
