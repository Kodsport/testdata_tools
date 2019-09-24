#!/usr/bin/env python3
# usage: python3 validator.py input_file correct_output output_dir < contestants_output

from decimal import *
import sys

def die(msg):
    print(msg)
    exit(43)

def accept():
    exit(42)

if len(sys.argv) < 4:
    exit(1)

answer_file = sys.argv[2]
output_dir = sys.argv[3]

with open(answer_file) as f:
    correct_answer = f.read()

correct_answer = Decimal(correct_answer)

try:
    given_answer = sys.stdin.read().strip()
except:
    die('unable to read stdin')

try:
    given_answer = Decimal(given_answer)
except:
    die('unable to convert answer to decimal')

if abs(given_answer - correct_answer) <= Decimal(10) ** -6:
    accept()
else:
    die('wrong!')
