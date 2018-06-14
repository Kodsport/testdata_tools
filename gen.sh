set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

SOLUTION_BASE=$PPATH/submissions/accepted

TOTAL_SCORE=0

# Set USE_PARALLEL=0 before including gen.sh to disable parallelism.
if [[ $USE_PARALLEL != 0 ]]; then
  USE_PARALLEL=1
  PARALLELISM_ACTIVE=1
fi

declare -A programs
declare -A cases
declare -A groups

get_ext () {
  echo $(echo $1 | rev | cut -d. -f1 | rev)
}

base () {
  ext=$(get_ext $1)
  echo `basename $1 .$ext`
}

# Add a program to the list of programs
# Arguments: name execution_command
add_program () {
  programs[$1]="$2"
}

add_program cat "bash -c cat<\$0"

# Compile a C++ program to run.
# Arguments: file opts
compile_cpp () {
  echo Compiling $1...
  if [[ $2 == *"opt"* ]]; then
    g++ -O2 -Wall -std=gnu++11 -DGENERATING_TEST_DATA -o $(base $1) $1
  else
    g++ -O2 -fsanitize=undefined -fsanitize=address -Wall -std=gnu++11 -DGENERATING_TEST_DATA -o $(base $1) $1
  fi
  add_program $(base $1) "./$(base $1)"
}

# Compile a Java program to run.
# Arguments: file
compile_java () {
  javac $1
  cp $(dirname $1)/*.class .
  add_program $(base $1) "java $(base $1)"
}

# Compile a Python program to run.
# Arguments: file opts
compile_py () {
  cp $1 $(base $1)
  if [[ $2 == *"pypy"* ]]; then
    add_program $(base $1) "pypy $(base $1)"
  else
    add_program $(base $1) "python3 $(base $1)"
  fi
}

# Compile a bash program to run.
# Arguments: file
compile_sh () {
  cp $1 $(base $1)
  add_program $(base $1) "bash $(base $1)"
}

# Compile a program
# Arguments: file opts
compile () {
  ext=$(get_ext $1)
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

update_scores() {
  echo "on_reject: continue
range: 0 $TOTAL_SCORE" > secret/testdata.yaml
  echo "range: 0 $TOTAL_SCORE
on_reject: continue
grader_flags: always_accept" > testdata.yaml
}

setup_dirs () {
  rm -rf secret
  mkdir -p sample secret
  echo "on_reject: continue
range: -1 0
accept_score: 0
grader_flags: no_errors" > sample/testdata.yaml
  update_scores
}

# Solve a test case using the solution
# Arguments: testcase path
solve () {
  execmd=${programs[$SOLUTION]}
  $($execmd < $1.in > $1.ans)
}

CURGROUP_NAME=-1
CURGROUP_DIR=invalid

# Use a certain solution as the reference solution
# Arguments: solution name
use_solution () {
  path=$SOLUTION_BASE/$1
  SOLUTION=$(base $path)
  compile $path $2
}


# Add the sample group:
# Arguments: none
samplegroup () {
  echo "Sample group"
  CURGROUP_DIR=sample
}

# Arguments: testcasename
sample () {
  echo "Solving case sample/$1..."
  solve sample/$1
}

cleanup_programs () {
  wait
  for i in "${!programs[@]}"
  do
    if [[ $i != cat ]]; then
      rm $i
    fi
  done
  rm -rf __pycache__
  rm -rf *.class
}

# Arguments: testgroupname score
group () {
  mkdir secret/$1
  CURGROUP_NAME=$1
  CURGROUP_DIR=secret/$1
  echo 
  echo "Group $CURGROUP_NAME ($1)"
  groups[$1]=""

  score=$2
  echo "on_reject: break
accept_score: $score
range: 0 $score
grader_flags: min" > secret/$1/testdata.yaml
  TOTAL_SCORE=$((TOTAL_SCORE + score))
  update_scores
}

# Arguments: parameters sent to input validator
limits () {
  echo "input_validator_flags: $@" >> $CURGROUP_DIR/testdata.yaml
}

do_tc () {
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

handle_err() {
  echo ERROR generating case $1
  # Kill the parent. This might fail if the other subprocesses do so at the
  # same time, but the PID is unlikely to be reused in this windows, so...
  # Just silence the error.
  kill $$ 2>/dev/null
  exit 1
}

par_tc () {
  set -E
  trap "handle_err $1" ERR
  do_tc "$@"
}

# Arguments: testcasename generator arguments...
tc () {
  name="$1"

  if [[ ${cases[$name]} != "" ]]
  then
    if [[ $# == 1 ]]; then
      if [[ ${cases[$name]} == $CURGROUP_NAME ]]; then
        echo "Skipping duplicate case secret/$name"
      else
        wait
        PARALLELISM_ACTIVE=1
        cp secret/${cases[$name]}/$name.in secret/${CURGROUP_NAME}/$name.in
        cp secret/${cases[$name]}/$name.ans secret/${CURGROUP_NAME}/$name.ans
        cases[$name]=$CURGROUP_NAME
        groups[$CURGROUP_NAME]="${groups[$CURGROUP_NAME]} $name"
        echo "Reusing secret/$name"
      fi
      return 0
    else
      echo "ERROR: duplicate test case name $name"
      exit 1
    fi
  fi

  cases[$name]=$CURGROUP_NAME
  groups[$CURGROUP_NAME]="${groups[$CURGROUP_NAME]} $name"

  program="${programs[$2]}"

  if [[ $USE_PARALLEL != 1 ]]; then
    do_tc "secret/$CURGROUP_NAME/$1" "$program" "${@:3}"
  else
    if [[ $PARALLELISM_ACTIVE = 5 ]]; then
      # wait after every 4 cases
      wait
      let PARALLELISM_ACTIVE=1
    fi
    let PARALLELISM_ACTIVE++
    par_tc "secret/$CURGROUP_NAME/$1" "$program" "${@:3}" &
  fi
}

# Arguments: ../custom-data/testcasename.in
custom () {
  tc $(base $1) cat $1
}

# Include all testcases in another group
# Arguments: group name to include
include_group () {
  any=0
  for x in ${groups[$1]}
  do
    tc $x
    any=1
  done
  if [[ $any = 0 ]]; then
    echo "ERROR: included group $1 does not exist"
    exit 1
  fi
}
