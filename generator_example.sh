#!/usr/bin/env bash
. ../../testdata_tools/gen.sh

# Example test data generator, with comments to explain what each line does.
# For a real problem, please remove the comments.

# For unlimited stack:
# ulimit -s unlimited

use_solution js_100.cpp              # Use ../submissions/accepted/js_100.cpp to generate answer files

# Compile generators
compile gen_random.py                # Add a generator 'gen_random' which invokes "python3 gen_random.py"
compile gen_complicated.py pypy      # 'gen_complicated' invokes "pypy gen_complicated.py"; faster than python3
compile gen_other.cpp opt            # C++ generator; opt means to compile with -O2 instead of debug flags

# Generate answers to sample cases
samplegroup
limits n=10
sample 1
sample 2
sample 3
sample_manual 4                      # Don't generate an .ans file for this sample (e.g. because there are multiple
                                     # solutions, and we want a specific one)

group group1 7                       # Add a new testdata group worth 7 points
limits n=15                          # Pass "n=15" to the input validator.
tc 1                                 # Reuse sample testcase 1
tc small-exact gen_random n=10       # Generate a testcase with name "exact" by running gen_random with arguments "n=10", "<some random number>".
                                     # (A deterministic, pseudo-random seed is automatically passed as the last argument.)
tc_manual ../manual-tests/hand1.in   # Add a hand-created testcase with name "hand1".
tc small-eleven1 gen_random n=11
tc small-eleven2 gen_random n=11
tc small-eleven3 gen_random n=11     # (etc. About 10-20 test cases per group is typical. The testcases will be run in order,
                                     # so it may be reasonable to put the slowest testcase first, and then WA-inducing ones.)

group group2 11
limits n=100
include_group group1                 # Mark group2 as including all of group 1. Always do this if it obeys the limits;
                                     # the testcases will still only be run once, so it doesn't hurt, and it will make
                                     # the test data stronger.
tc medium-exact1 gen_random n=100
tc medium-exact2 gen_random n=100
# etc.

group group3 12
limits n=100000 mode=special
include_group group1
tc medium-exact1                     # Reuse an individual testcase. Do this if include_group doesn't work due to special group constraints.
tc large-exact1 gen_random n=100000 mode=special
# etc.

group group4 70
limits n=100000
include_group group2                 # Including either group2 or group3 will transitively include group1; no need to specify it manually.
include_group group3
# etc.
