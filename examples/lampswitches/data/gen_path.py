from util import *

maxn = int(cmdlinearg('n'))
maxm = int(cmdlinearg('m'))
lens = list(map(int, cmdlinearg('len').split(',')))
if len(lens) == 1:
    lens *= 3

curn = 1
curm = 0
fails = 0
ed = [[] for _ in range(maxn)]
while True:
    up = random.randint(0, lens[0])
    mid = random.randint(0, lens[1])
    down = random.randint(0, lens[2])
    if curn + up + mid + down + 1 > maxn or curm + up + mid*2 + down + 4 > maxm:
        fails += 1
        if fails > 10:
            break
        else:
            continue
    ucur = curn - 1
    mcur = curn - 1
    dcur = curn - 1
    for i in range(up):
        ed[ucur].append(curn)
        ucur = curn
        curn += 1
    for i in range(mid):
        ed[mcur].append(curn)
        ed[curn].append(mcur)
        mcur = curn
        curn += 1
    for i in range(down):
        ed[curn].append(dcur)
        dcur = curn
        curn += 1
    ed[ucur].append(curn)
    ed[curn].append(dcur)
    ed[mcur].append(curn)
    ed[curn].append(mcur)
    curm += up + mid*2 + down + 4
    curn += 1

del ed[curn:]
output(ed, shuffled=True)
