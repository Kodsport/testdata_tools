import shutil
import os

cases = open("cases", "r")
groups = open("groups", "r")

group_cases = {}
for line in cases.readlines():
    case_name, group = line.strip().split()
    group = int(group)
    if group not in group_cases:
        group_cases[group] = []
    group_cases[group].append(case_name)

try:
    shutil.rmtree("cms-data")
except FileNotFoundError: pass
os.makedirs("cms-data")

scores = []

for i, line in enumerate(groups.readlines()):
    os.makedirs("cms-data/g%03d" % i)
    _, score = line.strip().split()
    score = int(score)
    scores.append((i, score))

    for x in group_cases[i]:
        shutil.copy("secret/%s.in" % x, "cms-data/g%03d/%s.in" % (i, x))
        shutil.copy("secret/%s.ans" % x, "cms-data/g%03d/%s.ans" % (i, x))

shutil.make_archive("cms", "zip", "cms-data")
shutil.rmtree("cms-data")

print('[' + ', '.join('[%d, %d]' % (x[1], len(group_cases[x[0]])) for x in scores) + ']')
