cases = open("cases", "r")
groups = open("groups", "r")

scores = []

for line in groups.readlines():
    groupname, score = line.strip().split()
    score = int(score)
    scores.append( (groupname, score ))

print('GROUP_SCORES = [' + ', '.join([str(x[1]) for x in scores]) + ']')

case_groups = {}

for line in cases.readlines():
    case_name, group = line.strip().split()
    if case_name not in case_groups:
        case_groups[case_name] = []
    group = int(group)
    case_groups[case_name].append(group)

sorted_cases = sorted(case_groups.items(), key = lambda x: x[0])

case_mapping = {}
for name, groups in sorted_cases:
    case_mapping[name] = len(case_mapping)

group_cases = [[] for x in scores]
for name, groups in case_groups.items():
    for group in groups:
        group_cases[group].append(str(case_mapping[name]))

print('GROUP_CASES = [' + ', '.join(['[' + ', '.join(cases) + ']' for cases in group_cases]) + ']')
grader = open("../../testdata_tools/grader.py", "r")
print(''.join(grader.readlines()))
