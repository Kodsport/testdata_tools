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

TOTAL_SCORE=0

declare -A programs
declare -A cases
declare -A basedir
declare -A groups
declare -a cleanup

_get_ext () {
  echo "$1" | rev | cut -d. -f1 | rev
}

_base () {
  ext=$(_get_ext "$1")
  echo $(basename "$1" .$ext)
}

_assert_scoring () {
  if [[ $USE_SCORING != 1 ]]; then
    echo "Do not call $1 for non-scoring generators"
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
  if [[ $2 == *"opt"* ]]; then
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
  echo "range: 0 $TOTAL_SCORE
on_reject: continue
grader_flags: ignore_sample" > testdata.yaml
}

# Solve a test case using the solution
# Arguments: testcase path
solve () {
  execmd=${programs[$SOLUTION]}
  $($execmd < $1.in > $1.ans)
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

# Arguments: testcasename
sample () {
  echo "Solving case sample/$1..."
  solve sample/$1
  cases[$1]=sample
  basedir[$1]=sample
  groups[sample]="${groups[sample]} $1"
}

# Arguments: testgroupname score
group () {
  _assert_scoring group
  mkdir secret/$1
  CURGROUP_NAME=$1
  CURGROUP_DIR=secret/$1
  echo 
  echo "Group $CURGROUP_NAME"
  groups[$1]=""

  score=$2
  echo "on_reject: break
accept_score: $score
range: 0 $score
grader_flags: min" > secret/$1/testdata.yaml
  TOTAL_SCORE=$((TOTAL_SCORE + score))
  _update_scores
}

# Arguments: parameters sent to input validator
limits () {
  if [[ $USE_SCORING == 1 ]]; then
    echo "input_validator_flags: $@" >> $CURGROUP_DIR/testdata.yaml
  else
    echo "input_validator_flags: $@" >> testdata.yaml
  fi
}

_do_tc () {
  name="$1"
  execmd="$2"
  # Let the seed be the 6 first hex digits of the hash of the name converted
  # to decimal (range 0-16777215), to make things more deterministic.
  seed=$((16#$(echo -n "$name" | md5sum | head -c 6)))
  echo "Generating case $name..."
  $execmd "${@:3}" $seed > "$name.in"

  echo "Solving case $name..."
  solve "$name"
}

_handle_err() {
  echo ERROR generating case $1
  # Kill the parent. This might fail if the other subprocesses do so at the
  # same time, but the PID is unlikely to be reused in this window, so...
  # Just silence the error.
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
  name="$1"
  if [[ $USE_SCORING == 1 && $CURGROUP_NAME == '.' ]]; then
    echo "ERROR: Test case $name must be within a test group"
    exit 1
  fi

  if [[ ${cases[$name]} != "" ]]
  then
    if [[ $# == 1 ]]; then
      if [[ ${cases[$name]} == $CURGROUP_DIR ]]; then
        echo "Skipping duplicate case secret/$name"
      else
        LN="ln -s ../../" # ln -sr isn't supported on Mac
        if [[ $USE_SYMLINKS = 0 ]]; then
          wait
          PARALLELISM_ACTIVE=1
          LN="cp "
        fi
        ${LN}${cases[$name]}/$name.in $CURGROUP_DIR/$name.in
        ${LN}${cases[$name]}/$name.ans $CURGROUP_DIR/$name.ans
        cases[$name]=$CURGROUP_DIR
        groups[$CURGROUP_NAME]="${groups[$CURGROUP_NAME]} $name"
        echo "Reusing ${basedir[$name]}/$name"
      fi
      return 0
    else
      echo "ERROR: duplicate test case name $name"
      exit 1
    fi
  else
    basedir[$name]=secret
  fi

  cases[$name]=$CURGROUP_DIR
  groups[$CURGROUP_NAME]="${groups[$CURGROUP_NAME]} $name"

  program="${programs[$2]}"

  if [[ $USE_PARALLEL != 1 ]]; then
    _do_tc "$CURGROUP_DIR/$1" "$program" "${@:3}"
  else
    if [[ $PARALLELISM_ACTIVE = 5 ]]; then
      # wait after every 4 cases
      wait
      let PARALLELISM_ACTIVE=1
    fi
    let PARALLELISM_ACTIVE++
    _par_tc "$CURGROUP_DIR/$1" "$program" "${@:3}" &
  fi
}

# Arguments: ../manual-tests/testcasename.in
tc_manual () {
  tc $(_base $1) cat $1
}

# Include all testcases in another group
# Arguments: group name to include
include_group () {
  _assert_scoring include_group
  any=0
  for x in ${groups[$1]}; do
    tc $x
    any=1
  done
  if [[ $any = 0 ]]; then
    echo "ERROR: included group $1 does not exist"
    exit 1
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
    rm -f $x
  done
  rm -rf __pycache__
  rm -rf *.class
}
trap _cleanup_programs EXIT
