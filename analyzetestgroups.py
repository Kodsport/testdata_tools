#!/usr/bin/env python3

# Assumptions:
# Correctness:
#  Secret groups are numbered data/secret/group1, data/secret/group2, ...
# Typographical (otherwise ugly output):
#  Times are <= 9.99s
#  At most 9 groups
#  Points are at most three digits

import re, sys, subprocess, yaml, argparse, itertools, logging, enum
from pathlib import Path
from collections import defaultdict, OrderedDict
from typing import List, Optional, Tuple, Dict


def parse_args():
    # Returns full path to problem directory and output of verifyproblem
    argsparser = argparse.ArgumentParser(
        description=r"""
            Summarise verifyproblem's log of a scoring problem built with testdata_tools.
            If submission source contains 
            '@EXPECTED_GRADES@ WA WA WA WA AC WA'
            somwhere, e.g., as a comment, also compare the outcome of secret test
            groups with the expected outcome.
            """
    )
    argsparser.add_argument("problemdir", help="Path to problem directory")
    argsparser.add_argument(
        "-f",
        "--file",
        dest="logfile",
        type=open,
        help="read logfile instead of running verifyproblem -l info",
    )
    argsparser.add_argument(
        "-n",
        "--no-warnings",
        help="don't show warnings",
        action="store_const",
        dest="loglevel",
        const=logging.ERROR,
        default=logging.WARNING,
    )
    return argsparser.parse_args()


class Pattern(enum.Enum):
    END_SUBMISSION = re.compile(
        r"""
        (?P<type>\S+)
        \s+
        submission
        \s+
        (?P<name>\S+)
        \s+
        \((?P<language>[^)]+)\)
        \s+
        (?P<status>\S+)
        \s+
        (?P<grade>\S+)
        \s+
        (\((?P<points>\d+)\)\s+)?
        \[.*CPU:\s(?P<maxtime>\d+.\d+)s.*\]
        """,
        re.VERBOSE,
    )
    FIRST_LINE = re.compile(r"Loading problem (?P<problemname>\S+)")
    TESTGROUP_GRADE = re.compile(
        r"""INFO\ :\ Grade\ on\ test\ case\ group\ data/
        (?P<type>sample|secret/group)
        ((?P<number>\d+))?
        \s+
        is
        \s+
        (?P<grade>\S+)""",
        re.VERBOSE,
    )
    START_SUBMISSION = re.compile(
        r"INFO : Check (?P<type>\S+) submission (?P<name>\S+)"
    )
    START_TESTGROUP = re.compile(
        r"INFO : Running on test case group data/(sample|secret/group(?P<number>\d+))"
    )
    AC_TC_RESULT = re.compile(
        r"""[T|t]est\ file\ result.*AC.*CPU:\s
        (?P<time>\d+.\d+)
        .*
        test\ case\ (sample|secret/group\d)/
        (?P<case>[^\]]+)
        """,
        re.VERBOSE,
    )
    TIMELIMIT = re.compile(
        r"setting timelim to (?P<limit>\d+) secs, safety margin to (?P<safety>\d+) secs"
    )


class Verdict:
    def __init__(self, grade, time=None):
        self.grade = grade
        if grade == "AC":
            self.time = time  # time can be None for AC sample group
        else:
            self.time = None

    def __str__(self):
        res = "\033[32m" if self.grade == "AC" else "\033[91m"
        res += f"{self.grade}\033[0m"
        if self.time is not None:
            res += f":{self.time}s"
        return res

    def __format__(self, f):
        return str(self).__format__(f)


class Submission:
    subdir = {
        "AC": "accepted",
        "PAC": "partially_accepted",
        "WA": "wrong_answer",
        "TLE": "time_limit_exceeded",
    }

    expected_score_pattern = re.compile(
        r"@EXPECTED_GRADES@ (?P<grades>((WA|AC|TLE|RTE|MLE)\s*)+)"
    )

    @staticmethod
    def _get_expected_grades(path: Path) -> Dict[str, str]:
        if path.is_file():
            with open(path, encoding="utf-8") as sourcefile:
                for l, line in enumerate(sourcefile):
                    m = Submission.expected_score_pattern.search(line)
                    if m:
                        gradelist = m.group("grades").split()
                        return {str(i + 1): g for (i, g) in enumerate(gradelist)}
        else:
            for child in path.iterdir():
                grades = Submission._get_expected_grades(child)
                if grades is not None:
                    return grades
                # TODO (low prio): Check for presence of multiple files containg grade hints
        return {}

    def __init__(self, problempath, expected_total_grade, name):
        self.problempath = problempath
        self.name = name
        self.expected_total_grade = expected_total_grade
        self.verdict: OrderedDict[str, Verdict] = {}
        self.maxtime: Optional[float] = None
        self.points: Optional[int] = None
        path = (
            problempath
            / "submissions"
            / Path(Submission.subdir[self.expected_total_grade])
            / self.name
        )
        self.expected_grades: Dict[str, str] = Submission._get_expected_grades(path)
        if self.expected_grades and expected_total_grade == "AC":
            logging.warning(
                f"AC submission {self} contains EXPECTED_GRADES. "
                "(Ignored, consider removing it.)"
            )

    def __str__(self):
        return self.name  # TODO: Maybe this should include language


class Problem:
    def __init__(self, problempath, inputstream):
        self.submissions: List[Submission] = []

        s = tc_id = None
        lineno = max_group_id = 0
        for line in inputstream:
            lineno += 1
            for p in Pattern:
                match = p.value.search(line)
                if match:
                    break
            else:
                continue
            d = match.groupdict()
            if p == Pattern.FIRST_LINE:
                problemname = d["problemname"]
                if problemname != problempath.stem:
                    exit(
                        f"FATAL: Problem directory does not match log file ({problemname}). Aborting..."
                    )
                with open(problempath / "problem.yaml", encoding="utf-8") as file:
                    problemtype = yaml.safe_load(file).get("type")
                    if problemtype != "scoring":
                        exit(
                            f"FATAL: {problemname} is is not a scoring problem. Aborting..."
                        )
                print(" " * 80, end="\r")
                print(f"\033[01mScoring problem: {problemname}\033[0m")
            elif p == Pattern.START_SUBMISSION:
                s = Submission(problempath, d["type"], d["name"])
            elif p == Pattern.START_TESTGROUP:
                tc_times: List[float] = []
            elif p == Pattern.AC_TC_RESULT:
                print(problemname, s, end="\r")
                tc_times.append(float(d["time"]))
                tc_id = d["case"]
            elif p == Pattern.TESTGROUP_GRADE:
                grade = d["grade"]
                assert s is not None
                if d["type"] == "sample":
                    s.verdict["sample"] = Verdict(
                        grade, max(tc_times) if len(tc_times) else None
                    )
                else:
                    if grade == "AC" and len(tc_times) == 0:
                        logging.error(
                            f"{lineno} of verifyproblem: "
                            f"AC grade for secret group requires at least one test case"
                        )
                    group_id = int(d["number"])
                    max_group_id = max(group_id, max_group_id)
                    s.verdict[str(group_id)] = Verdict(grade, max(tc_times))
            elif p == Pattern.END_SUBMISSION:
                assert s is not None
                s.points = int(d["points"] or "0")
                s.maxtime = float(d["maxtime"])
                self.submissions.append(s)
            elif p == Pattern.TIMELIMIT:
                self.timelimits = int(d["limit"]), int(d["safety"])
            statusline = f"Submission {s}, test case {tc_id}"
            print(" " * 80, end="\r")
            print(statusline[:80], end="\r")

        self.groups = list(str(i) for i in range(1, max_group_id + 1))
        allgroups = ["sample"] + self.groups
        for s in self.submissions:
            if list(s.verdict.keys()) != allgroups:  # Note: this is order-sensitive
                logging.error(f"Unexpected group name for submission {s}.")


def print_table(log):
    suggestions: List[Tuple[Submission, str]] = []  # suggested EXPECTED_GRADES
    warnings: Dict[Submission, list[int]] = defaultdict(list)
    alignto = max(len(str(sub)) for sub in log.submissions)
    if alignto < len("Submission"):
        alignto = len("Submission")
    print("\033[01m", end="")
    print(f"{'Submission':{alignto}} Sample  ", end=" ")
    print(" ".join(f"Group {i} " for i in log.groups), end=" ")
    print("Pts Time  Expected\033[0m")
    for s in log.submissions:
        print(f"{s.name:{alignto}}", end=" ")
        for verdict in s.verdict.values():
            print(f"{verdict:17}", end=" ")
        print(f"{s.points:3}", end=" ")
        print(f"{s.maxtime:4.2f}s", end=" ")

        if s.expected_total_grade == "AC":
            s.expected_grades = {i: "AC" for i in log.groups}
        if s.expected_grades:
            summary = []
            for i in log.groups:
                if s.expected_grades[i] == s.verdict[i].grade:
                    summary.append("\033[32my\033[0m")
                else:
                    summary.append("\033[91mn\033[0m")
                    warnings[s].append(i)
        else:
            summary = ["."] * len(log.groups)
            all_grades = [v.grade for v in s.verdict.values()]
            suggestions.append((s, " ".join(all_grades[1:])))
        print("".join(summary))
    if warnings:
        for s, warngroups in warnings.items():
            for i in warngroups:
                logging.warning(
                    f"{s}: Unexpected grade {s.verdict[i].grade} on test group {i}. "
                    f"(Expected {s.expected_grades[i]})."
                )
    if suggestions:
        for s, expectations in suggestions:
            logging.warning(
                f"{s}: No hint found. Consider adding '@EXPECTED_GRADES@ {expectations}'."
            )


def check_distinguished(log):
    accepting_subs = defaultdict(list)
    for s in log.submissions:
        for i, v in s.verdict.items():
            if v.grade == "AC":
                accepting_subs[i].append(s)
    ok = True
    for i, j in itertools.combinations(log.groups, 2):
        if accepting_subs[i] == accepting_subs[j]:
            logging.warning(
                f"No submission distinguishes test groups {i} and {j}. "
                "Consider adding one, or merging groups."
            )
            ok = False
    if ok:
        print(
            "\033[32mOK: \033[0mAll secret test groups distinguished by some submission"
        )


def main():
    args = parse_args()
    logging.basicConfig(
        format="\033[91m%(levelname)s: \033[0m %(message)s", level=args.loglevel
    )
    if not args.logfile:
        verifyproblem = subprocess.Popen(
            ["verifyproblem", args.problemdir, "-l info"],
            stdout=subprocess.PIPE,
            encoding="utf-8",
            universal_newlines=True,
            bufsize=1,
        )
        print("Running", " ".join(verifyproblem.args), "...", end="\r")
        inputstream = verifyproblem.stdout
    else:
        inputstream = args.logfile
    problempath = Path(args.problemdir).resolve()

    problem = Problem(problempath, inputstream)

    problem.submissions.sort(key=lambda d: (-d.points, d.maxtime))

    print_table(problem)
    print(f"Time limit: {problem.timelimits[0]}s, safe: {problem.timelimits[1]}s")
    check_distinguished(problem)


if __name__ == "__main__":
    main()
