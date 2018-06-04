#!/bin/bash
PPATH=$(realpath ..)
. ../../testdata_tools/gen.sh

# Setup testdata.yaml and do some cleanup
setup_dirs

# Choose your solution
use_solution js_100.cpp

# Compile generators
compile random.py # Arguments: length seed

# Generate answers to sample cases (optional)
samplegroup
sample 1
sample 2
sample 3

# Add a new testdata group
group group1 7
# Note: tc automatically adds a deterministic, pseudo-random seed argument to your generator
tc exact random 10
tc one_off_01 random 11
tc one_off_02 random 11
tc one_off_03 random 11

group group2 11
include_group group1

group group3 12
include_group group2

group group4 20
include_group group3

# Cleanup programs
cleanup_programs
