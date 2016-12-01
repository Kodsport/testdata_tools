#!/bin/bash
PPATH=$(realpath ..)
. ../../testdata_tools/gen.sh

# Setup testdata.yaml and do some cleanup
setup_dirs

# Choose your solution
use_solution js_100.cpp

# Compile generators
compile random.py # Arguments: length seed

# Generate answers to sample cases
samplegroup
sample sample01_trivial
sample sample02_example
sample sample03_single

# Add a new testdata group
group simple 7
# Note: tc automatically adds a deterministic, pseudo-random seed argument to your generator
tc exact random 10
tc one_off_01 random 11
tc one_off_02 random 11
tc one_off_03 random 11

group cubic 11
include_group simple

group quadratic 12
include_group cubic

group nlogn 20
include_group quadratic

# Cleanup programs
cleanup_programs

# Generate grader
generate_grader
