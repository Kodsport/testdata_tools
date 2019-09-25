#!/usr/bin/env python3
directed = True
if directed:
    print("digraph G {")
else:
    print("graph G {")
n = int(input())
for i in range(n):
    eds = map(int, input().split()[1:])
    for j in eds:
        if directed:
            print(i+1, '->', j)
        else:
            print(i+1, '--', j)
print("}")
