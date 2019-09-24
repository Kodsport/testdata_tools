#!/usr/bin/env bash
. ../../../gen.sh

use_solution ../../data/empty.sh # empty .ans files

compile echo.sh

samplegroup
# no samples

group group1 30
limits mode=one
tc one-1 echo one
tc one-2 echo one
tc one-3 echo one
tc one-4 echo one

group group2 30
limits mode=two
tc two-1 echo two
tc two-2 echo two
tc two-3 echo two
tc two-4 echo two

group group3 40
limits mode=random
for A in {1..20}; do
	tc random-$A echo random
done
