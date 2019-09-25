from util import *

n = int(cmdlinearg('n'))
m = int(cmdlinearg('m'))
mode = cmdlinearg('mode')

while True:
    ed = [[] for _ in range(n)]
    seen = set()
    i = 0
    while len(seen) < m:
        a = random.randrange(n)
        b = random.randrange(n)
        i = len(seen)
        if i == 0: a = 0
        if i == 1: a = n-1
        if i == 2: b = 0
        if i == 3: b = n-1
        if a == b or (a,b) in seen:
            continue
        seen.add((a,b))
        ed[a].append(b)

    possible = reachable(ed, 0, n-1) and reachable(ed, n-1, 0)
    if mode == 'possible' and possible:
        break
    if mode == 'impossible' and not possible:
        break

output(ed, shuffled=True)
