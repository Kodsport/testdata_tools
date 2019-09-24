#!/usr/bin/python3

# Example generator, prints n and then n numbers in the range 1 to 1000.

import sys
import random

def cmdlinearg(name, default=None):
    for arg in sys.argv:
        if arg.startswith(name + "="):
            return arg.split("=")[1]
    if default is None:
        print("missing parameter", name)
        sys.exit(1)
    return default

random.seed(int(cmdlinearg('seed', sys.argv[-1])))
n = int(cmdlinearg('n'))

ar = [random.randint(1, 1000) for _ in range(n)]
print(n)
print(*ar)
