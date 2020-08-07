#!/usr/bin/env python3
# @EXPECTED_GRADES@ AC AC AC AC
from decimal import *

a, b, c = map(Decimal, input().split())
print(a * b / c)
