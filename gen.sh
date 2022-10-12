# This file provides support functions for generating testdata, primarily for
# scoring problems with test groups. It has some niceties like automatically
# passing deterministic random seeds to the generator, and generating test
# data in parallel.
#
# See generator_example.sh for example usage.

set -e

# Set USE_PARALLEL=0 before including gen.sh to disable parallelism.
if [[ $USE_PARALLEL != 0 ]]; then
  USE_PARALLEL=1
  PARALLELISM_ACTIVE=1
fi

# Set USE_SCORING=0 before including gen.sh to indicate a non-scoring problem.
if [[ $USE_SCORING != 0 ]]; then
  USE_SCORING=1
fi

# Set REQUIRE_SAMPLE_REUSE=0 before including gen.sh to indicate that it's
# fine for samples not to be included in any test groups.
if [[ $REQUIRE_SAMPLE_REUSE != 0 ]]; then
  REQUIRE_SAMPLE_REUSE=$USE_SCORING
fi

# Feature-detect symlink support if not explicitly set.
if [[ $USE_SYMLINKS = '' ]]; then
  set +e
  rm -f .dummy .dummy2
  ln -s .dummy .dummy2 2>/dev/null
  echo -n test >.dummy
  if [[ $(cat .dummy2 2>/dev/null) = test ]]; then
    USE_SYMLINKS=1
  else
    USE_SYMLINKS=0
  fi
  rm -f .dummy .dummy2
  set -e
fi

PROBLEM_PATH=$(realpath ..)
SOLUTION_BASE=$PROBLEM_PATH/submissions/accepted

RED='\033[0;31m'
NOCOL='\033[0m'

TOTAL_SCORE=0
HAS_ERROR=0
TC_INDEX=1

declare -A programs
declare -A cases
declare -A latestdir
declare -A nicenames
declare -A groups
declare -a cleanup

_get_ext () {
  echo "$1" | rev | cut -d. -f1 | rev
}

_base () {
  ext=$(_get_ext "$1")
  echo $(basename "$1" .$ext)
}

_error () {
  echo -e "${RED}ERROR: $1${NOCOL}" >&2
  HAS_ERROR=1
}

_assert_scoring () {
  if [[ $USE_SCORING != 1 ]]; then
    _error "Do not call $1 for non-scoring generators"
    exit 1
  fi
}

# Add a program to the list of programs
# Arguments: name execution_command
add_program () {
  programs[$1]="$2"
}

# Mark a file as needing to be removed when the generator finishes.
add_cleanup () {
  cleanup+=("$1")
}

# By default, 'cat' is a supported program. Prefer tc_manual rather than
# relying on this, though. (The reason for the weird syntax is that we
# want to ignore the last parameter this holds the seed.)
add_program cat "bash -c cat<\$0"

# Compile a C++ program to run.
# Arguments: file opts
compile_cpp () {
  echo Compiling $1...
  if [[ $2 == *"opt"* || "$(uname -s)" != Linux* ]]; then
    g++ -O2 -Wall -std=gnu++14 -DGENERATING_TEST_DATA -o $(_base $1) $1
  else
    g++ -O2 -fsanitize=undefined -fsanitize=address -Wall -std=gnu++14 -DGENERATING_TEST_DATA -o $(_base $1) $1
  fi
  add_program $(_base $1) "./$(_base $1)"
  add_cleanup $(_base $1)
}

# Compile a Java program to run.
# Arguments: file
compile_java () {
  javac $1
  cp $(dirname $1)/*.class .
  add_program $(_base $1) "java $(_base $1)"
  add_cleanup $(_base $1)
}

# Compile a Python program to run.
# Arguments: file opts
compile_py () {
  if [[ $2 == *"pypy"* ]]; then
    add_program $(_base $1) "pypy $1"
  elif [[ $2 == *"python2"* ]]; then
    add_program $(_base $1) "python2 $1"
  else
    add_program $(_base $1) "python3 $1"
  fi
}

# Compile a bash program to run.
# Arguments: file
compile_sh () {
  add_program $(_base $1) "bash $1"
}

# Compile a program
# Arguments: file opts
compile () {
  ext=$(_get_ext $1)
  if [ $ext == "java" ]
  then 
    compile_java $1
  elif [ $ext == "cpp" -o $ext == "cc" ]
  then
    compile_cpp $1 $2
  elif [ $ext == "py" ]
  then
    compile_py $1 $2
  elif [ $ext == "sh" ]
  then
    compile_sh $1 $2
  else
    echo "Unsupported program: $1"
    exit 1
  fi
}

_update_scores() {
  _assert_scoring "_update_scores"
  echo "on_reject: continue
range: 0 $TOTAL_SCORE
grader_flags: first_error accept_if_any_accepted" > secret/testdata.yaml
  echo "on_reject: continue
range: 0 $TOTAL_SCORE
grader_flags: ignore_sample" > testdata.yaml
}

# Solve a test case using the solution
# Arguments: testcase path
solve () {
  local execmd=${programs[$SOLUTION]}
  $execmd < $1.in > $1.ans
}

CURGROUP_NAME=.
CURGROUP_DIR=secret

# Use a certain solution as the reference solution
# Arguments: solution name
use_solution () {
  path=$SOLUTION_BASE/$1
  SOLUTION=$(_base $path)
  compile $path $2
}


# Add the sample group:
# Arguments: none
samplegroup () {
  _assert_scoring samplegroup
  echo "Sample group"
  CURGROUP_DIR=sample
}

# Add a sample testcase
# Arguments: testcasename
sample () {
  local name="$1"
  local path="sample/$1"
  if [[ ${cases[$name]} != "" ]]; then
    _error "duplicate test case \"$path\""
    return 0
  fi
  echo "Solving case sample/$name..."
  solve "sample/$name"
  cases[$name]="$path"
  latestdir[$name]=sample
  nicenames[$name]="sample/$name"
  groups[sample]="${groups[sample]} $name"
}

# Add a sample testcase, with manual .ans file
# Arguments: testcasename
sample_manual () {
  local name="$1"
  local path="sample/$1"
  if [[ ${cases[$name]} != "" ]]; then
    _error "duplicate test case \"$path\""
    return 0
  fi
  for ext in in ans; do
    if [[ ! -f "$path.$ext" ]]; then
      _error "tried to add manual sample testcase $path, but .$ext file is missing"
      return 0
    fi
  done
  echo "Using manual solution for $path"
  cases[$name]="$path"
  latestdir[$name]=sample
  nicenames[$name]="sample/$name"
  groups[sample]="${groups[sample]} $name"
}

# Arguments: testgroupname score
group () {
  _assert_scoring group
  CURGROUP_NAME="$1"
  CURGROUP_DIR="secret/$1"
  echo 
  echo -e "Group $CURGROUP_NAME"
  mkdir "$CURGROUP_DIR"
  groups[$1]=""

  score=$2
  echo "on_reject: break
accept_score: $score
range: 0 $score
grader_flags: min" > "$CURGROUP_DIR/testdata.yaml"
  TOTAL_SCORE=$((TOTAL_SCORE + score))
  _update_scores
}

# Arguments: parameters sent to input validator
limits () {
  if [[ $USE_SCORING == 1 ]]; then
    echo "input_validator_flags: $@" >> "$CURGROUP_DIR/testdata.yaml"
  else
    echo "input_validator_flags: $@" >> testdata.yaml
  fi
}

output_validator_flags () {
  if [[ $USE_SCORING == 1 ]]; then
    echo "output_validator_flags: $@" >> "$CURGROUP_DIR/testdata.yaml"
  else
    echo "output_validator_flags: $@" >> testdata.yaml
  fi
}

_check_missing_samples () {
  for INF in sample/*.in; do
    local name=$(basename "$INF" .in)
    if [[ "$name" != '*' && ${cases[$name]} != sample* ]]; then
      _error "missing sample or sample_manual directive for sample/$name.in"
    fi
  done

  local any=0
  for INF in sample/*.in; do
    local name=$(basename "$INF" .in)
    if [[ "$name" != '*' && ${cases[$name]} = sample* && ${latestdir[$name]} = "sample" && $REQUIRE_SAMPLE_REUSE = 1 ]]; then
      _error "sample/$name must be included in some secret test group; add the line \"tc $name\""
      any=1
    fi
  done
  if [[ $any = 1 ]]; then
    echo "(Add \"REQUIRE_SAMPLE_REUSE=0\" before including gen.sh to ignore this, if needed.)"
  fi
}

_do_tc () {
  local nicename="$1"
  local name="$2"
  local path="$3"
  local execmd="$4"
  # Let the seed be the 6 first hex digits of the hash of the name converted
  # to decimal (range 0-16777215), to make things more deterministic.
  seed=$((16#$(echo -n "$name" | md5sum | head -c 6)))
  echo "Generating case $nicename..."
  $execmd "${@:5}" $seed > "$path.in"

  echo "Solving case $nicename..."
  solve "$path"
}

_handle_err() {
  _error "crashed while generating case $1"
  # Stop the entire bash process. It will still run _cleanup_programs and wait
  # for all parallel tasks for now.
  kill $$ 2>/dev/null
  exit 1
}

_par_tc () {
  set -E
  trap "_handle_err $1" ERR
  _do_tc "$@"
}

# Arguments: testcasename generator arguments...
tc () {
  local name="$1"
  if [[ $USE_SCORING == 1 && "$CURGROUP_NAME" == '.' ]]; then
    _error "test case \"$name\" must be within a test group"
    exit 1
  fi

  if [[ $# == 1 ]]; then
    # Reuse test case
    if [[ ${cases[$name]} != "" ]]; then
      if [[ ${latestdir[$name]} == "$CURGROUP_DIR" ]]; then
        echo "Skipping duplicate case ${nicenames[$name]}"
      else
        LN="ln -s ../../" # ln -sr isn't supported on Mac
        if [[ $USE_SYMLINKS = 0 ]]; then
          wait
          PARALLELISM_ACTIVE=1
          LN="cp "
        fi
        local path="$CURGROUP_DIR/$(_base ${cases[$name]})"
        ${LN}${cases[$name]}.in "$path.in"
        ${LN}${cases[$name]}.ans "$path.ans"
        latestdir[$name]="$CURGROUP_DIR"
        groups[$CURGROUP_NAME]="${groups[$CURGROUP_NAME]} $name"
        echo "Reusing ${nicenames[$name]}"
      fi
    else
      _error "tried to reuse test case \"$name\" which doesn't exist"
    fi
    return 0
  else
    # New test case
    if [[ ${cases[$name]} != "" ]]; then
      _error "duplicate test case name \"$name\""
      return 0
    fi
  fi

  # Add an index to the test case name, to enforce evaluation order.
  local path="$CURGROUP_DIR/$(printf '%03d' $TC_INDEX)-$name"
  let TC_INDEX++
  cases[$name]="$path"
  latestdir[$name]="$CURGROUP_DIR"
  local nicename="$CURGROUP_NAME/$name"
  nicenames[$name]="$nicename"
  groups[$CURGROUP_NAME]="${groups[$CURGROUP_NAME]} $name"

  local program="${programs[$2]}"
  if [ ! "$program" ]; then
    _error "missing compile command for generator \"$2\""
    return 0
  fi

  if [[ $USE_PARALLEL != 1 ]]; then
    _do_tc "$nicename" "$name" "$path" "$program" "${@:3}"
  else
    if [[ $PARALLELISM_ACTIVE = 5 ]]; then
      # wait after every 4 cases
      wait
      let PARALLELISM_ACTIVE=1
    fi
    let PARALLELISM_ACTIVE++
    _par_tc "$nicename" "$name" "$path" "$program" "${@:3}" &
  fi
}

# Arguments: ../manual-tests/testcasename.in
tc_manual () {
  local name="$2"
  if [[ $# == 1 ]]; then
      name=$(_base "$1")
  fi
  tc $(_base "$1") cat "$1"
}

# Include all testcases in another group
# Arguments: group name to include
include_group () {
  _assert_scoring include_group
  local any=0
  for x in ${groups[$1]}; do
    tc "$x"
    any=1
  done
  if [[ $any = 0 ]]; then
    _error "included group \"$1\" does not exist"
  fi
}

# Initialization and cleanup code, automatically included.
_setup_dirs () {
  rm -rf secret
  mkdir -p sample secret
  if [[ $USE_SCORING == 1 ]]; then
    echo "on_reject: continue
range: 0 0
accept_score: 0
grader_flags: first_error" > sample/testdata.yaml
    _update_scores
  fi
}
_setup_dirs

_cleanup_programs () {
  wait
  for x in "${cleanup[@]}"; do
    rm -f "$x"
  done
  rm -rf __pycache__
  rm -rf *.class

  _check_missing_samples

  if [[ $HAS_ERROR = 1 ]]; then
    echo
    echo "There were errors, see above."
    exit 1
  fi
}
trap _cleanup_programs EXIT
