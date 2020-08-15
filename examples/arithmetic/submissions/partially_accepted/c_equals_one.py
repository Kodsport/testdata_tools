#!/usr/bin/env python3
# @EXPECTED_GRADES@ WA WA AC WA
from decimal import Decimal

a, b, _ = map(Decimal, input().split())
print(a * b / 1)
