from util import *

n = int(cmdlinearg('n'))
maxm = int(cmdlinearg('m'))
mode = cmdlinearg('mode')
special = int(cmdlinearg('special', 0))

line = (mode == 'line')

def gen_dir(n):
    res = [[] for _ in range(n)]
    maxi = 0
    reachable = [False] * n
    reachable[0] = True
    for i in range(n-1):
        if line:
            if special:
                co = random.choice([0,0,0,0,1,1,2,2,3,4,4,5,6,7,8])
            else:
                co = random.choice([0,0,0,0,1,1,2,2,3,4,4,5])
            if i == maxi and co == 0:
                co = 2
            co = min(co, n-1 - i)
            ivs = range(i+1, i+1 + co)
        else:
            co = max(0, random.randint(-1, 4))
            if i == maxi and co == 0:
                co = 2
            if special:
                ivs = [i + x for x in random.sample([1,2,3,4,5,6,7,8,9], co)]
            else:
                ivs = [i + x for x in random.sample([1,2,3,4,5,6], co)]
        ivs = [x for x in ivs if x < n]
        if not ivs and i == maxi:
            ivs.append(n-1)
        for j in ivs:
            if reachable[i]:
                reachable[j] = True
                maxi = max(maxi, j)
            res[i].append(j)
    return res

def rev(res):
    n = len(res)
    return remap(res, list(reversed(range(n))))

def gen_sparse_dir(n, skip):
    skips = list(map(int, skip.split(',')))
    skipa = skips[0]
    skipb = skips[-1]
    spl = nonzerosplit(n, skipa * 2 + 1)
    which = random.sample(range(skipa), skipb)
    pre = 0
    ren = []
    for i, v in enumerate(spl):
        iv = list(range(pre, pre+v))
        pre += v
        if i % 2 == 1 and (i // 2) in which:
            continue
        ren.extend(iv)

    res = gen_dir(len(ren))
    return remap(res, ren, n)

if mode == 'somelong':
    left = gen_dir(n)
    right = rev(left)
    res = [[] for _ in range(n)]
    for i in range(n):
        res[i] = left[i] + right[i]
    jumps = int(cmdlinearg('jumps'))
    jumplen = int(cmdlinearg('jumplen'))
    ju = nonzerosplit(jumplen, jumps)
    for le in ju:
        le = min(le, n-1)
        a = random.randrange(n - le)
        b = a + le
        if random.choice([True, False]):
            a,b = b,a
        res[a].append(b)

elif mode == 'line':
    left = gen_dir(n)
    right = rev(gen_dir(n))
    res = merge(left, right)

elif mode == 'standard':
    skips = cmdlinearg('skip', '0').split(':')
    left = gen_sparse_dir(n, skips[0])
    right = gen_sparse_dir(n, skips[-1])
    ren = list(reversed(range(n)))
    revs = list(map(int, cmdlinearg('rev', '0').split(',')))
    reva = revs[0]
    revb = revs[-1]
    spl = nonzerosplit(n, reva * 2 + 1)
    which = random.sample(range(reva), revb)
    pre = 0
    ren2 = []
    for i, v in enumerate(spl):
        iv = ren[pre : pre+v]
        if i % 2 == 1 and (i // 2) in which:
            iv.reverse()
        ren2.extend(iv)
        pre += v
    right = remap(right, ren2)
    res = merge(left, right)

else:
    assert False, "Unrecognized mode"

if line:
    for i, ed in enumerate(res):
        ed.append(i)
        ed.sort()
        assert ed[-1] - ed[0] == len(ed) - 1
        assert len(ed) == len(set(ed))
        ed.remove(i)
    output(res, shuffled=False)
elif cmdlinearg('shuffled', '1') == '1':
    output(res, shuffled=True)
else:
    output(res, shuffled=False)

su = 0
for row in res:
    su += len(row)
if su > maxm:
    print("too many edges", su, maxm, file=sys.stderr)
    assert False
