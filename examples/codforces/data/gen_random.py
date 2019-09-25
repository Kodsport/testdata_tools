#!/usr/bin/env pypy
#First placing one of each type, then randomizing the rest.

from __future__ import print_function
import sys
import random

def cmdlinearg(name, default=None):
    for arg in sys.argv:
        if arg.startswith(name + "="):
            return arg.split("=")[1]
    assert default is not None, name
    return default

random.seed(int(cmdlinearg('seed', sys.argv[-1])))
n = int(cmdlinearg('n'))
k = int(cmdlinearg('k', random.randint(1, n)))
sort = int(cmdlinearg('sort', 0))

v = list(range(1, k+1)) + [random.randint(1, k) for _ in range(n-k)]
if sort == 0:
  random.shuffle(v)
else:
  v.sort()
  if sort == -1:
    v.reverse()

split = random.randrange(0, n)
v = v[split:] + v[:split]

print(n, k)
print(" ".join(map(lambda x: str(x), v)))
