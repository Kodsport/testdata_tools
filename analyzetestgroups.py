#!/usr/bin/env python3
"""
 Provides a human-readable summary of the output of
    verifyproblem <problemdir> -l info
 for use with scoring problems and mutiple test groups.
 ompares the actual grades determined by verifyproblem with expected
 grades specified in the submission source code (if found).
 Also checks that each pair of test groups is actually distinguished
 by some submission.

 Example:
    $ python3 analyzetestgroups.py examples/arithmetic
    Analyzing problem: arithmetic
    WARNING: AC submission arithmetic.py contains EXPECTED_GRADES. (Ignored, consider removing it.)
    Submission        Sample   Group 1  Group 2  Group 3  Group 4  Pts Time  Expected
    arithmetic.cpp    AC:0.01s AC:0.01s AC:0.01s AC:0.01s AC:0.01s 100 0.01s yyyy
    arithmetic.py     AC:0.03s AC:0.03s AC:0.03s AC:0.04s AC:0.04s 100 0.04s yyyy
    arithmetic_ld.cpp WA       AC:0.01s AC:0.01s AC:0.0s  WA        75 0.01s ....
    arithmetic_dir    WA       AC:0.0s  AC:0.0s  WA       WA        50 0.00s yyyy
    arithmetic_d.cpp  WA       AC:0.0s  AC:0.01s WA       WA        50 0.01s ....
    c_equals_one.py   WA       WA       WA       AC:0.03s WA        25 0.03s yyyy
    slowmult.py       TLE      AC:0.03s TLE      TLE      TLE       25 3.11s ynyy
    false.py          RTE      RTE      RTE      RTE      RTE        0 0.03s yyyy
    WARNING: slowmult.py: Unexpected grade TLE on test group 2. (Expected AC).
    INFO: arithmetic_ld.cpp: No hint found. Consider adding '@EXPECTED_GRADES@ AC AC AC WA'.
    INFO: arithmetic_d.cpp: No hint found. Consider adding '@EXPECTED_GRADES@ AC AC WA WA'.
    Time limit: 1s, safe: 2s
    OK: All secret test groups distinguished by some submission

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
from enum import Enum, auto
from pathlib import Path
from collections import defaultdict, OrderedDict
from typing import List, Optional, Union, Tuple, Dict, Callable, Pattern, TextIO

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


class Grade(Enum):
    """Test group grade, i.e., the grade that a submission can get on a single test group."""

    AC = auto()
    WA = auto()
    TLE = auto()
    RTE = auto()
    JE = auto()

    def __str__(self):
        """AC is green, everything else is red"""
        res = "\033[32m" if self == Grade.AC else "\033[91m"
        return res + f"{self.name}\033[0m"


class SubmissionType(Enum):
    """The type of a submission is the *expected* final grades, as
    indicated by its placement in subdirectory.
            <problemname>/submissions/<subdir_grade>/name
    In verifyproblem.py, this is called the expected_verdict of the submission.
    """

    AC = "accepted"
    PAC = "partially_accepted"
    WA = "wrong_answer"
    RTE = "run_time_error"
    TLE = "time_limit_exceeded"


class Verdict:
    """The grader's verdict for a single test group, such as AC:3.21s or WA

    Attributes:
        grade (Grade): the grade
        time (float): Slowest time for any test case in this group. Else None.

    Attribute time is only non-None for AC grades. Note that time can
    be None even for AC grades (e.g., empty sample input in an interactive problem).
    """

    def __init__(self, grade: Grade, time=None):
        self.grade = grade
        self.time = time if grade == Grade.AC else None

    def __str__(self):
        res = str(self.grade)
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
        type (SubmissionType): the expected final grade for all test groups,
            as indicated by the submission's subdiretory
        verdict (OrderedDict[str, Verdict]): maps test group names
            "sample", "1", "2", ... to their Verdict.
            Keys are  in that order.
        maxtime (Tuple[float, float]): (timelimit, safe time limit) as determined
            by verifyproblem
        points (int): The total number of points as determined by Verifyproblem.
    """

    expected_score_pattern = re.compile(
        r"@EXPECTED_GRADES@ (?P<grades>((WA|AC|TLE|RTE|JE)\s*)+)"
    )

    @staticmethod
    def _get_expected_grades(path: Path) -> Dict[str, Grade]:
        if path.is_file():
            with open(path, encoding="utf-8") as sourcefile:
                for line in sourcefile:
                    match = Submission.expected_score_pattern.search(line)
                    if match:
                        gradelist = (Grade[g] for g in match.group("grades").split())
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
        return self.type == SubmissionType.AC or len(self._expected_grades)

    def expected_grade(self, i: str) -> Grade:
        """Returns the expected grade on secret group i."""
        if self.type == SubmissionType.AC:
            return Grade.AC
        return self._expected_grades[i]

    def __init__(self, problempath, stype: SubmissionType, name: str):
        self.name = name
        self.type: SubmissionType = stype
        self.verdict: Dict[
            str, Verdict
        ] = OrderedDict()  # Note: the type is collections.OrderedDict
        self.maxtime: Optional[float] = None
        self.points: Optional[int] = None
        path = problempath / "submissions" / Path(self.type.value) / self.name
        self._expected_grades: Dict[str, Grade] = Submission._get_expected_grades(path)
        if len(self._expected_grades) > 0 and self.type == SubmissionType.AC:
            logging.warning(
                "AC submission %s contains EXPECTED_GRADES. "
                "(Ignored, consider removing it.)",
                self,
            )

    def __str__(self):
        return self.name


class VerificationLogParser:
    """Parse output from verifyproblem <path> -l info.

    VerificationLogParser.parse() works line by line through given inputstream,
    matches the current line to various regular expressions in the list
    VerificationLogParser.pattern and dispatches to class methods accordingly,
    slowly building a proper Problem object in self.problem.

    Performs various sanity checks on the log to stay in sync.
    """

    def __init__(self, problem):
        self.problem: Problem = problem
        self.tc_times = None  # list of AC times of current test group
        self.tc_id = None  # current testcase id
        self.sub = None  # current submission
        self.lineno = 0
        self.max_group_id = 0  # largest secret group ID yet seen

    def parse(self, inputstream: TextIO) -> None:
        """Parse all of inputstream, incrementally building self.problem"""
        for line in inputstream:
            self.lineno += 1
            self.parseline(line)

    def parseline(self, line: str) -> None:
        """Dispatch the given line among the class methods, based on which
        VerificationLogParser.pattern matches.
        """
        for fun, pattern in VerificationLogParser.patterns.items():
            match = pattern.search(line)
            if match:
                fun(self, match.groupdict())
                statusline = f"Submission {self.sub}, test case {self.tc_id}"
                print(" " * 80, end="\r")
                print(statusline[:80], end="\r")

    def _first_line(self, matchgroup):
        """Loading problem <problemname>"""
        self.problem.name = matchgroup["problemname"]
        if self.problem.name != self.problem.path.stem:
            sys.exit(
                f"FATAL: Problem directory does not match log file ({self.problem.name})."
                "Aborting..."
            )
        print(" " * 80, end="\r")
        print(f"\033[01mAnalyzing problem: {self.problem.name}\033[0m")

    def _start_submission(self, matchgroup):
        """INFO : Check <type> submission <name>")"""
        self.sub = Submission(
            self.problem.path, SubmissionType[matchgroup["type"]], matchgroup["name"]
        )

    def _start_testgroup(self, _):
        r"INFO : Running on test case group data/(sample|secret/group<number>)"
        self.tc_times: List[float] = []

    def _ac_tc_result(self, matchgroup):
        """Test file result ... AC ... <time> ... test case ... <case>"""
        print(self.problem.name, self.sub, end="\r")
        self.tc_times.append(float(matchgroup["time"]))
        self.tc_id = matchgroup["case"]

    def _testgroup_grade(self, matchgroup):
        """INFO : Grade on test case group ... <type> ... <number> is <grade>"""
        assert self.sub is not None
        grade = Grade[matchgroup["grade"]]
        time = max(self.tc_times) if len(self.tc_times) > 0 else None
        if matchgroup["type"] == "sample":
            self.sub.verdict["sample"] = Verdict(grade, time)
        else:
            i = matchgroup["number"]
            self.sub.verdict[i] = Verdict(grade, time)
            if grade == Grade.AC and time is None:
                logging.error(
                    "Line %d of verifyproblem: "
                    "AC grade for secret group %d requires at least one test case",
                    self.lineno,
                    i,
                )
            self.max_group_id = max(int(i), self.max_group_id)

    def _end_submission(self, matchgroup):
        """<type> submission <name> (<language>) (<status>) (<grade>) <points> ...CPU: <maxtime>"""
        assert self.sub is not None
        self.sub.points = int(matchgroup["points"] or "0")
        self.sub.maxtime = float(matchgroup["maxtime"])
        self.problem.submissions.append(self.sub)

    def _timelimit(self, matchgroup):
        """setting timelim to <limit> secs, safety margin to <safety> secs"""
        self.problem.timelimits = int(matchgroup["limit"]), int(matchgroup["safety"])

    patterns: Dict[Callable, Pattern] = {
        _first_line: re.compile(r"Loading problem (?P<problemname>\S+)"),
        _testgroup_grade: re.compile(
            r"""INFO\ :\ Grade\ on\ test\ case\ group\ data/
        (?P<type>sample|secret/group)
        ((?P<number>\d+))?
        \s+ is \s+
        (?P<grade>\S+)""",
            re.VERBOSE,
        ),
        _start_submission: re.compile(
            r"INFO : Check (?P<type>\S+) submission (?P<name>\S+)"
        ),
        _start_testgroup: re.compile(
            r"INFO : Running on test case group data/(sample|secret/group(?P<number>\d+))"
        ),
        _ac_tc_result: re.compile(
            r"""[T|t]est\ file\ result.*AC.*CPU:\s
        (?P<time>\d+.\d+)
        .* test\ case\ (sample|secret/group\d)/
        (?P<case>[^\]]+)
        """,
            re.VERBOSE,
        ),
        _timelimit: re.compile(
            r"setting timelim to (?P<limit>\d+) secs, safety margin to (?P<safety>\d+) secs"
        ),
        _end_submission: re.compile(
            r"""
        (?P<type>\S+)
        \s+ submission \s+
        (?P<name>\S+)
        \s+
        \((?P<language>.*)\)
        \s+
        (?P<status>OK with extra time:|OK:|got|\S+)
        \s+
        (?P<grade>\S+)
        \s+
        (\((?P<points>\d+)\)\s+)?
        \[.*CPU:\s(?P<maxtime>\d+.\d+)s.*\]
        """,
            re.VERBOSE,
        ),
    }


class Problem:
    """A problem.

    Attributes:
        name (str): the problem's name, say "hello"
        path (Path): the problem path, say Path("../kattis_stuff/hello")
        submissions (List[Submissions]): the submissions making up this problem
        groups (List[str]): the secret test groups, ["1", "2", ...]
        timelimits (Tuple[int, int]): the timelimit and safe timelimit determined
            by verifyproblem
    """

    def __init__(self, problempath, inputstream: Union[TextIO]):
        self.path = problempath
        self.submissions: List[Submission] = []
        self.timelimits = None, None

        parser = VerificationLogParser(self)
        parser.parse(inputstream)

        # sanity check: make sure every submission has verdicts for
        # "sample", "1", "2", ... and that the number of groups is consistent
        self.groups = list(str(i) for i in range(1, parser.max_group_id + 1))
        allgroups = ["sample"] + self.groups
        for sub in self.submissions:
            if list(sub.verdict.keys()) != allgroups:  # Note: verdict is ordered dict
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
        for sub in sorted(self.submissions, key=lambda d: (-d.points, d.maxtime)):
            print(f"{sub.name:{alignto}}", end=" ")
            for verdict in sub.verdict.values():
                print(f"{verdict:17}", end=" ")
            print(f"{sub.points:3}", end=" ")
            print(f"{sub.maxtime:4.2f}s", end=" ")

            if sub.has_expected_grades():
                summary = []
                for i in self.groups:
                    if sub.expected_grade(i) == sub.verdict[i].grade:
                        summary.append("\033[32my\033[0m")
                    else:
                        summary.append("\033[91mn\033[0m")
                        warnings[sub].append(i)
            else:
                summary = ["."] * len(self.groups)
                all_grades = [str(Grade(v.grade)) for v in sub.verdict.values()]
                suggestions.append((sub, " ".join(all_grades[1:])))
            print("".join(summary))
        for sub, warngroups in warnings.items():
            for i in warngroups:
                logging.warning(
                    "%s: Unexpected grade %s on test group %s. " "(Expected %s).",
                    sub,
                    sub.verdict[i].grade,
                    i,
                    sub.expected_grade(i),
                )
        for sub, expectations in suggestions:
            logging.info(
                "%s: No hint found. Consider adding '@EXPECTED_GRADES@ %s'.",
                sub,
                expectations,
            )

    def check_distinguished(self):
        """Check if all secrete test groups are distinguished by some submission.
        Emit warning otherwise.
        """
        accepting_subs = defaultdict(list)
        for sub in self.submissions:
            for i, verdict in sub.verdict.items():
                if verdict.grade == Grade.AC:
                    accepting_subs[i].append(sub)
        all_distinguished = True
        for i, j in itertools.combinations(self.groups, 2):
            if accepting_subs[i] == accepting_subs[j]:
                logging.warning(
                    "No submission distinguishes test groups %s and %s. "
                    "Consider adding one, or merging groups.",
                    i,
                    j,
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
            logging.critical(
                "%s is not a scoring problem. Aborting...", args.problemdir
            )
            sys.exit(1)
    if not args.logfile:
        verifyproblem = subprocess.Popen(
            ["verifyproblem", args.problemdir, "-l", "info", "-p", "submissions"],
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
    problem.print_table()
    print(f"Time limit: {problem.timelimits[0]}s, safe: {problem.timelimits[1]}s")
    problem.check_distinguished()


if __name__ == "__main__":
    main()
