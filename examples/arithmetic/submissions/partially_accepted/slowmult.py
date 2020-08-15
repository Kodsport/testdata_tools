#!/usr/bin/env python3

""" Following line of expected grades falsely assumes that
    test group 2 is accepted.
    analyzetestgroups.py should detect this and emit a warning.
    @EXPECTED_GRADES@ AC AC TLE TLE
"""
from decimal import Decimal

a, b, c = map(Decimal, input().split())

def slowmult(x, y):
    res = 0
    for _ in range(int(x)):
        for _ in range(int(y)):
            res += 1
    return Decimal(res)

print(slowmult(a, b) / c)
