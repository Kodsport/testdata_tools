#!/usr/bin/env python3
"""
 Provides a human-readable summary of the output of
    verifyproblem <problemdir> -l info
 for use with scoring problems and mutiple test groups.
 Compares the actual grades determined by verifyproblem with expected
 grades specified in the submission source code (if found).
 Also checks that each pair of test groups is actually distinguished
 by some submission.

 Example:
 $ python3 analyzetestgroups.py examples/arithmetic2
 Analyzing problem: arithmetic2
 WARNING: AC submission arithmetic.py contains EXPECTED_GRADES. (Ignored, consider removing it.)
 Submission        Sample   Group 1  Group 2  Group 3  Group 4  Pts Time  Expected
 arithmetic.cpp    AC:0.01s AC:0.0s  AC:0.01s AC:0.01s AC:0.01s 100 0.01s yyyy
 arithmetic.py     AC:0.05s AC:0.05s AC:0.05s AC:0.05s AC:0.05s 100 0.05s yyyy
 arithmetic_ld.cpp WA       AC:0.01s AC:0.01s AC:0.01s WA        75 0.01s yyny
 arithmetic_d.cpp  WA       AC:0.01s AC:0.01s WA       WA        50 0.01s ....
 arithmetic_dir    WA       AC:0.02s AC:0.02s WA       WA        50 0.02s yyyy
 WARNING: arithmetic_ld.cpp: Unexpected grade AC on test group 3. (Expected WA).
 INFO: arithmetic_d.cpp: No hint found. Consider adding '@EXPECTED_GRADES@ AC AC WA WA'.
 Time limit: 1s, safe: 2s
 WARNING: No submission distinguishes test groups 1 and 2. Consider adding one, or merging groups.

 Verbosity can be specified using --loglevel ('info', 'warning', 'error').

 Since running verifyproblem can be very time-consuming, its output can
 be provided as a file, as in:
 $ verifyproblem myproblem -l info > tmplog.txt
 $ python3 analyzetestgroups.py --file tmplog.txt

 Assumptions:
     Correctness:
         Secret groups are numbered data/secret/group1, data/secret/group2, ...
     Typographical (otherwise ugly output):
         Times are <= 9.99s
         At most 9 groups
         Points are at most three digits
"""

import sys
import re
import subprocess
import argparse
import itertools
import logging
from enum import Enum
from pathlib import Path
from collections import defaultdict, OrderedDict
from typing import List, Optional, Tuple, Dict

import yaml


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

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
        "-l",
        "--loglevel",
        help="set the logger's verbosity threshold (default 'info')",
        choices=["info", "warning", "error"],
        default="info",
    )
    return argsparser.parse_args()


class Pattern(Enum):
    """Regular expressions needed for parsing the output of

            verifyproblem <problemdir> -l info.
    """

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
    """The grader's verdict for a single test group.

    Attributes:
        grade (str): One of 'AC', 'WA', 'TLE', 'RTE', 'JE'
        time (float): Slowest time for any test case in this group. Else None.

    Attribute time is only non-None for AC grades. Note that time can
    be None even for AC grades (e.g., empty sample input in an interactive problem).
    """
    def __init__(self, grade, time=None):
        self.grade = grade
        if grade == "AC":
            self.time = time
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
    """A single submission, typically a source file, and its evaluation
    by verifyproblem.

    Attributes:
        name: the submission name, typically a source file or a directory
        expected_total_grade: the expected final grade for all test groups,
            one of 'AC', 'PAC', 'WA', 'RTE', TLE' as indicated by the placement
            of the submission in the directory structure:
            <problemname>/submissions/<expected_total_grade>/name
            In verifyproblem.py this is called expected_verdict.
        verdict (OrderedDict[str, Verdict]): maps test group names
            "sample", "1", "2", ... to their Verdict.
            Keys are  in that order.
        maxtime (Tuple[float, float]): (timelimit, safe time limit) as determined
            by verifyproblem
        points (int): The total number of points as determined by Verifyproblem.
    """
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
                for line in sourcefile:
                    match = Submission.expected_score_pattern.search(line)
                    if match:
                        gradelist = match.group("grades").split()
                        return {str(i + 1): g for (i, g) in enumerate(gradelist)}
        else:
            for child in path.iterdir():
                grades = Submission._get_expected_grades(child)
                if grades is not None:
                    return grades
        return {}

    def has_expected_grades(self):
        """True if this submission specifies expected grades.
        This is specified by a string like
            @EXPECTED_GRADES@ AC AC WA TLE
        in the submission's source file.
        If expected_total_grade is "AC", the expected grade for every test
        group is "AC" no matter what the source file says.
        Empty if no such line is found.
        """
        return self.expected_total_grade == "AC" or len(self._expected_grades)

    def expected_grade(self, i):
        """Returns the expected grade on secret group i."""
        if self.expected_total_grade == "AC":
            return "AC"
        return self._expected_grades[i]

    def __init__(self, problempath, expected_total_grade, name):
        self.name = name
        self.expected_total_grade = expected_total_grade
        self.verdict: Dict[str, Verdict] = OrderedDict() # Note: the type is collections.OrderedDict
        self.maxtime: Optional[float] = None
        self.points: Optional[int] = None
        path = (
            problempath
            / "submissions"
            / Path(Submission.subdir[self.expected_total_grade])
            / self.name
        )
        self._expected_grades: Dict[str, str] = Submission._get_expected_grades(path)
        if len(self._expected_grades) > 0 and expected_total_grade == "AC":
            logging.warning(
                "AC submission %s contains EXPECTED_GRADES. "
                "(Ignored, consider removing it.)",
                self
            )

    def __str__(self):
        return self.name


class Problem:
    """A problem.

    Attributes:
        submissions (List[Submissions]): the submissions making up this problem
        groups (List[str]): the secret test groups, "1", "2", ...
        timelimits (Tuple[int, int]): the timelimit and safe timelimit determined
            by verifyproblem
    """

    @staticmethod
    def _find_matching_pattern(line):
        """Returns a match object that matches the given line, or None"""
        for pat in Pattern:
            match = pat.value.search(line)
            if match:
                return pat, match
        return None, None

    def __init__(self, problempath, inputstream):
        self.submissions: List[Submission] = []

        sub = tc_id = None
        lineno = max_group_id = 0
        for line in inputstream:
            lineno += 1
            pattern, match = Problem._find_matching_pattern(line)
            if match is None:
                continue
            d = match.groupdict()
            if pattern == Pattern.FIRST_LINE:
                problemname = d["problemname"]
                if problemname != problempath.stem:
                    sys.exit(
                        f"FATAL: Problem directory does not match log file ({problemname})."
                        "Aborting..."
                    )
                print(" " * 80, end="\r")
                print(f"\033[01mAnalyzing problem: {problemname}\033[0m")
            elif pattern == Pattern.START_SUBMISSION:
                sub = Submission(problempath, d["type"], d["name"])
            elif pattern == Pattern.START_TESTGROUP:
                tc_times: List[float] = []
            elif pattern == Pattern.AC_TC_RESULT:
                print(problemname, sub, end="\r")
                tc_times.append(float(d["time"]))
                tc_id = d["case"]
            elif pattern == Pattern.TESTGROUP_GRADE:
                assert sub is not None
                sub.verdict["sample" if d["type"] == "sample" else d["number"]] = Verdict(
                    d["grade"], max(tc_times) if len(tc_times) > 0 else None
                )
                if d["type"] != "sample":
                    if d["grade"] == "AC" and len(tc_times) == 0:
                        logging.error(
                            "Line %d of verifyproblem: "
                            "AC grade for secret group requires at least one test case",
                            lineno
                        )
                    max_group_id = max(int(d["number"]), max_group_id)
            elif pattern == Pattern.END_SUBMISSION:
                assert sub is not None
                sub.points = int(d["points"] or "0")
                sub.maxtime = float(d["maxtime"])
                self.submissions.append(sub)
            elif pattern == Pattern.TIMELIMIT:
                self.timelimits = int(d["limit"]), int(d["safety"])
            statusline = f"Submission {sub}, test case {tc_id}"
            print(" " * 80, end="\r")
            print(statusline[:80], end="\r")

        self.groups = list(str(i) for i in range(1, max_group_id + 1))
        allgroups = ["sample"] + self.groups
        for sub in self.submissions:
            if list(sub.verdict.keys()) != allgroups:  # Note: this is order-sensitive
                logging.error("Unexpected group name for submission %s.", sub)


    def print_table(self):
        """Print a table of verdicts for each submission, and possibly emit
        some warnings and suggestions.
        """
        suggestions: List[Tuple[Submission, str]] = []  # suggested EXPECTED_GRADES
        warnings: Dict[Submission, List[int]] = defaultdict(list)
        alignto = max(len(str(sub)) for sub in self.submissions + ["Submission"])
        print("\033[01m", end="")
        print(f"{'Submission':{alignto}} Sample  ", end=" ")
        print(" ".join(f"Group {i} " for i in self.groups), end=" ")
        print("Pts Time  Expected\033[0m")
        for sub in self.submissions:
            print(f"{sub.name:{alignto}}", end=" ")
            for verdict in sub.verdict.values():
                print(f"{verdict:17}", end=" ")
            print(f"{sub.points:3}", end=" ")
            print(f"{sub.maxtime:4.2f}s", end=" ")

            if sub.has_expected_grades:
                summary = []
                for i in self.groups:
                    if sub.expected_grade(i) == sub.verdict[i].grade:
                        summary.append("\033[32my\033[0m")
                    else:
                        summary.append("\033[91mn\033[0m")
                        warnings[sub].append(i)
            else:
                summary = ["."] * len(self.groups)
                all_grades = [v.grade for v in sub.verdict.values()]
                suggestions.append((sub, " ".join(all_grades[1:])))
            print("".join(summary))
        for sub, warngroups in warnings.items():
            for i in warngroups:
                logging.warning(
                    "%s: Unexpected grade %s on test group %s. "
                    "(Expected %s).",
                    sub, sub.verdict[i].grade, i, sub.expected_grade(i)
                )
        for sub, expectations in suggestions:
            logging.info(
                "%s: No hint found. Consider adding '@EXPECTED_GRADES@ %s'.",
                sub, expectations
            )


    def check_distinguished(self):
        """Check if all secrete test groups are distinguished by some submission.
        Emit warning otherwise.
        """
        accepting_subs = defaultdict(list)
        for sub in self.submissions:
            for i, verdict in sub.verdict.items():
                if verdict.grade == "AC":
                    accepting_subs[i].append(sub)
        all_distinguished = True
        for i, j in itertools.combinations(self.groups, 2):
            if accepting_subs[i] == accepting_subs[j]:
                logging.warning(
                    "No submission distinguishes test groups %s and %s. "
                    "Consider adding one, or merging groups.", i, j
                )
            all_distinguished = False
        if all_distinguished:
            print(
                "\033[32mOK: \033[0mAll secret test groups distinguished by some submission"
            )


def main():
    """Parse (typically invoking verifyproblem as a subprocess), analyze, print."""
    args = parse_args()

    logging.basicConfig(
        format="\033[91m%(levelname)s:\033[0m %(message)s",
        level={
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
        }[args.loglevel],
    )
    with open(Path(args.problemdir) / "problem.yaml", encoding="utf-8") as file:
        problemtype = yaml.safe_load(file).get("type")
        if problemtype != "scoring":
            logging.critical("%s is not a scoring problem. Aborting...", args.problemdir)
            sys.exit(1)
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

    problem.print_table()
    print(f"Time limit: {problem.timelimits[0]}s, safe: {problem.timelimits[1]}s")
    problem.check_distinguished()


if __name__ == "__main__":
    main()
