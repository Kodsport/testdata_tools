import sys
import random

def cmdlinearg(name, default=None):
    for arg in sys.argv:
        if arg.startswith(name + "="):
            return arg.split("=")[1]
    assert default is not None, name
    return default

random.seed(int(cmdlinearg('seed', sys.argv[-1])))

def reachable(eds, a, b):
    seen = set()
    q = [a]
    while q:
        x = q.pop()
        if x in seen:
            continue
        seen.add(x)
        if x == b:
            return True
        for y in eds[x]:
            q.append(y)
    return False

def nonzerosplit(n, k):
    li = [0] + sorted(random.sample(range(1, n), k-1)) + [n]
    res = []
    for (a, b) in zip(li, li[1:]):
        res.append(b-a)
    return res

def merge(left, right):
    n = len(left)
    assert n == len(right)
    res = [[] for _ in range(n)]
    for i in range(n):
        res[i] = left[i] + right[i]
    return res

def remap(res, ren, m=None):
    n = len(res)
    if m is None:
        m = n
    res2 = [[] for _ in range(m)]
    for i in range(n):
        res2[ren[i]] = [ren[x] for x in res[i]]
    return res2

def output(res, shuffled):
    n = len(res)
    if shuffled:
        for i in range(n):
            res[i] = list(set(res[i]))
        ren = list(range(1, n - 1))
        random.shuffle(ren)
        ren = [0] + ren + [n-1]
        res = remap(res, ren)
        for i in range(n):
            random.shuffle(res[i])

    print(n)
    sumlen = 0
    for i, li in enumerate(res):
        assert i not in li
        li = [x + 1 for x in li]
        random.shuffle(li)
        print(len(li), *li)
        sumlen += len(li)
    print('m =', sumlen, file=sys.stderr)
