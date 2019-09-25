#!/usr/bin/env bash

. ../../../gen.sh

ulimit -s unlimited

use_solution fh_nlgn.cpp opt

compile gen_random.py

MAXN=200000

samplegroup
limits n=$MAXN k=$MAXN
sample 1
sample 2
sample 3

group group1 15
limits n=100 k=100
include_group sample
tc n100_1 gen_random n=100 k=25
tc n100_2 gen_random n=100 k=50
tc n100_3 gen_random n=100 k=75
tc n100_4 gen_random n=100 k=100
tc n100_5 gen_random n=100
tc n100_6 gen_random n=100
tc n100_sort_7 gen_random n=100 sort=1
tc n100_sortReverse_8 gen_random n=100 sort=-1


group group2 20
limits n=1000 k=1000
include_group group1
tc n1000_1 gen_random n=1000 k=25
tc n1000_2 gen_random n=1000 k=50
tc n1000_3 gen_random n=1000 k=75
tc n1000_4 gen_random n=1000 k=100
tc n1000_5 gen_random n=1000
tc n1000_6 gen_random n=1000
tc n1000_sort_7 gen_random n=1000 sort=1
tc n1000_sortReverse_8 gen_random n=1000 sort=-1

group group3 25
limits n=$MAXN k=$MAXN kEqualsN=1
tc kEqualsN_1 gen_random n=$MAXN k=$MAXN
tc kEqualsN_2 gen_random n=$MAXN k=$MAXN
tc kEqualsN_3 gen_random n=$MAXN k=$MAXN
tc kEqualsN_4 gen_random n=$MAXN k=$MAXN
tc kEqualsN_5 gen_random n=$MAXN k=$MAXN
tc kEqualsN_6 gen_random n=$MAXN k=$MAXN
tc kEqualsN_sort_7 gen_random n=$MAXN k=$MAXN sort=1
tc kEqualsN_sortReverse_8 gen_random n=$MAXN k=$MAXN sort=-1

group group4 40
limits n=$MAXN k=$MAXN
include_group group1
include_group group2
include_group group3
tc noRestr_1 gen_random n=$MAXN k=$((MAXN / 2))
tc noRestr_2 gen_random n=$MAXN k=$((MAXN * 2 / 3))
tc noRestr_3 gen_random n=$MAXN k=$((MAXN * 3 / 4))
tc noRestr_4 gen_random n=$MAXN
tc noRestr_5 gen_random n=$MAXN
tc noRestr_6 gen_random n=$MAXN
tc noRestr_7 gen_random n=$MAXN sort=1
tc noRestr_8 gen_random n=$MAXN sort=-1
