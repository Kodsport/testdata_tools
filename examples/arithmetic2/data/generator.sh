#!/usr/bin/env bash
. ../../../gen.sh

use_solution arithmetic.cpp

compile gen_random.py

samplegroup
limits ab=1e9 c=1e9
sample_manual 1
sample_manual 2
sample_manual 3
sample_manual 4

group group1 25
limits ab=10 c=10
tc 1
tc tiny-01 gen_random a=1 b=1 c=1
tc tiny-02 gen_random a=1 b=1 c=-7
tc tiny-03 gen_random a=10 b=10 c=10
tc tiny-04 gen_random a=10 b=10 c=10
tc tiny-05 gen_random a=10 b=10 c=10

group group2 25
limits ab=1e4 c=1e4
include_group group1
tc 2
tc small-01 gen_random a=1 b=1 c=10000
tc small-02 gen_random a=10000 b=10000 c=1
tc small-03 gen_random a=10000 b=10000 c=7
tc small-04 gen_random a=10000 b=10000 c=-7
tc small-05 gen_random a=10000 b=10000 c=10000
tc small-06 gen_random a=10000 b=10000 c=10000

group group3 25
limits ab=1e9 c=1
tc 2
tc 3
tc tiny-01
tc mult-02 gen_random a=1000000000 b=1000000000 c=1
tc mult-03 gen_random a=1000000000 b=1000000000 c=1
tc mult-04 gen_random a=1000000000 b=1000000000 c=1
tc mult-05 gen_random a=1000000000 b=1000000000 c=1

group group4 25
limits ab=1e9 c=1e9
include_group group2
include_group group3
tc 4
tc large-01 gen_random a=1000000000 b=1000000000 c=-1
tc large-02 gen_random a=-1000000000 b=-1000000000 c=-3
tc large-03 gen_random a=-1000000000 b=-1000000000 c=-7
tc large-04 gen_random a=1000000000 b=1000000000 c=-7
tc large-05 gen_random a=1000000000 b=1000000000 c=1000000000
tc large-06 gen_random a=1000000000 b=1000000000 c=1000000000
tc large-07 gen_random a=1000000000 b=1000000000 c=1000000000
tc large-08 gen_random a=1000000000 b=1000000000 c=1000000000
