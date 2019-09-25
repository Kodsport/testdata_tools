#!/usr/bin/env bash

. ../../../gen.sh

use_solution sl.cpp

compile gen_random.py
compile gen_lr.py
compile gen_path.py

samplegroup
limits n=50 m=200
sample 1
sample 2
sample 3

group group1 13
limits n=15 m=60
include_group sample
tc small-imp gen_random n=15 m=50 mode=impossible
tc small-rand1 gen_random n=5 m=10 mode=possible
tc small-rand2 gen_random n=10 m=30 mode=possible
tc small-rand3 gen_random n=10 m=30 mode=possible
tc small-rand4 gen_random n=15 m=60 mode=possible
tc small-rand5 gen_random n=15 m=60 mode=possible
tc small-lr1 gen_lr n=15 m=60 mode=standard
tc small-lr2 gen_lr n=15 m=60 rev=2 mode=standard
tc small-lr3 gen_lr n=15 m=60 rev=6 mode=standard
tc small-lr4 gen_lr n=14 m=60 rev=3 skip=3 mode=standard
tc small-lr5 gen_lr n=15 m=60 jumps=4 jumplen=8 mode=somelong
tc small-path1 gen_path n=15 m=60 len=2
tc small-path2 gen_path n=15 m=60 len=3
tc small-path3 gen_path n=15 m=60 len=3
tc small-path4 gen_path n=15 m=60 len=3
tc small-path5 gen_path n=15 m=60 len=4 seed=11
tc small-path6 gen_path n=15 m=60 len=5,2,5
tc small-path7 gen_path n=15 m=60 len=2,5,2
tc_manual ../manual-tests/tworev.in

group group2 33
limits n=50 m=200
include_group group1
tc med-imp1 gen_random n=50 m=200 mode=impossible
tc med-rand1 gen_random n=50 m=200 mode=possible
tc med-lr1 gen_lr n=50 m=200 rev=2 mode=standard
tc med-lr2 gen_lr n=50 m=200 rev=7 mode=standard
tc med-lr3 gen_lr n=50 m=200 rev=7 skip=5 mode=standard
tc med-lr4 gen_lr n=50 m=200 jumps=7 jumplen=50 mode=somelong
tc med-path gen_path n=50 m=200 len=5

group group3 34
limits n=500 m=2000 line=1
tc line-1 gen_lr n=500 m=2000 mode=line
tc line-2 gen_lr n=10  m=2000 mode=line
tc line-3 gen_lr n=40  m=2000 mode=line
tc line-4 gen_lr n=500 m=2000 mode=line
tc line-5 gen_lr n=320 m=2000 special=1 mode=line seed=43

group group4 20
limits n=500 m=2000
include_group group2
tc large-imp1 gen_random n=500 m=2000 mode=impossible
tc large-rand1 gen_random n=500 m=2000 mode=possible
tc large-lr1 gen_lr n=500 m=2000 rev=2 mode=standard
tc large-lr2 gen_lr n=500 m=2000 rev=50 mode=standard
tc large-lr3 gen_lr n=500 m=2000 rev=50 skip=20,8 mode=standard
tc large-lr4 gen_lr n=500 m=2000 jumps=7 jumplen=500 mode=somelong
tc large-path gen_path n=500 m=2000 len=5

# Wait for threads to finish
wait

# Create visualizations; Kattis shows these to judges when a submission fails
if which dot >/dev/null; then
	echo Creating visualizations...
	for F in sample/*.in secret/group1/*.in; do
		N=$(head -n 1 $F)
		if [[ $N -lt 25 ]]; then
			./visualize.py <$F | dot -T png -o ${F%.in}.png
		fi
	done
fi
