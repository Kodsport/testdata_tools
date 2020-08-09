#!/usr/bin/env python3

import random
import sys

def cmdlinearg(name, default=None):
    for arg in sys.argv:
        if arg.startswith(name + "="):
            return arg.split("=")[1]
    if default is None:
        print("missing parameter", name)
        sys.exit(1)
    return default

random.seed(int(cmdlinearg('seed', sys.argv[-1])))
lim_a = int(cmdlinearg('a'))
lim_b = int(cmdlinearg('b'))
lim_c = int(cmdlinearg('c'))

def rand(lim):
    if lim > 0:
        return random.randint(1, lim)
    return -lim

print("{} {} {}".format(rand(lim_a), rand(lim_b), rand(lim_c)))
