import sys

def main():
    if "ignore" in sys.argv:
        print "AC 0"
    elif "groups" in sys.argv:
        verdicts = []
        scores = []
        for line in sys.stdin.readlines():
            verdict, score = line.split()
            verdicts.append(verdict)
            scores.append(float(score) if verdict == "AC" else 0.0)
        total_score = 0
        first_error = None
        for group in range(len(GROUP_SCORES)):
            group_score = GROUP_SCORES[group]
            rel_score = 1.0
            for case in GROUP_CASES[group]:
                rel_score = min(rel_score, scores[case])
                if verdicts[case] != "AC" and not first_error:
                    first_error = verdicts[case]
            total_score += group_score * rel_score
        total_score = round(total_score * 100.0) / 100.0
        if total_score == 0.0 and first_error:
            print "%s 0" % first_error
        else:
            print "AC %f" % total_score
    elif "sum" in sys.argv:
        total_score = 0
        first_error = None
        for line in sys.stdin.readlines():
            verdict, score = line.split()
            total_score += float(score)
            if verdict != "AC" and not first_error:
                first_error = verdict
        total_score = round(total_score * 100.0) / 100.0
        if total_score == 0 and first_error:
            print "%s 0" % first_error
        else:
            print "AC %f" % total_score
    else:
        for line in sys.stdin.readlines():
            print line

main()
