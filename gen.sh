set -e

SOLUTION_BASE=$PPATH/submissions/accepted

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
  programs[$1]=$2
}

# Compile a C++ program to run.
# Arguments: file
compile_cpp () {
  g++ -O2 -Wall -std=gnu++11 -o $(base $1) $1
  add_program $(base $1) "./$(base $1)"
}

# Compile a Java program to run.
# Arguments: file
compile_java () {
  javac $1
  add_program $(base $1) "java $(base $1)"
}

# Compile a Python program to run.
# Arguments: file
compile_py () {
  cp $1 $(base $1)
  add_program $(base $1) "python3 $(base $1)"
}

# Compile a program
# Arguments: file
compile () {
  ext=$(get_ext $1)
  if [ $ext == "java" ]
  then 
    compile_java $1
  elif [ $ext == "cpp" -o $ext == "cc" ]
  then
    compile_cpp $1
  elif [ $ext == "py" ]
  then
    compile_py $1
  else
    echo "Unsupported program: $1"
    exit 1
  fi
}

setup_dirs () {
  rm -f groups cases
  mkdir -p secret
  echo "grading: custom
grader_flags: ignore" > sample/testdata.yaml
  echo "grading: custom
grader_flags: groups" > secret/testdata.yaml
}

# Solve a test case using the solution
# Arguments: testcase path
solve () {
  execmd=${programs[$SOLUTION]}
  $($execmd < $1.in > $1.ans)
}

CURGROUP=-1
CURGROUP_NAME=-1
SEED=58723

# Use a certain solution as the reference solution
# Arguments: solution name
use_solution () {
  path=$SOLUTION_BASE/$1
  SOLUTION=$(base $path)
  compile $path
}


# Add the sample group:
# Arguments: none
samplegroup () {
  echo "Sample group"
}

# Arguments: testcasename
sample () {
  echo "Solving case sample/$1..."
  solve sample/$1
}

cleanup_programs () {
  for i in "${!programs[@]}"
  do
    rm $i
  done
  rm -rf __pycache__
}

# Arguments testgroupname score
group () {
  CURGROUP_NAME=$1
  CURGROUP=$(( CURGROUP+1 ))
  echo 
  echo "Group $CURGROUP ($1)"
  echo $1 $2 >> groups
  groups[$1]=""
}

# Arguments: testcasename generator arguments...
tc () {
  groups[$CURGROUP_NAME]="${groups[$CURGROUP_NAME]} $1"
  echo $1 $CURGROUP >> cases
  if [[ ${cases[$1]} == "yes" ]]
  then
    echo "Reusing secret/$1"
    return 0
  fi
  SEED=$(( SEED+1 ))
  echo "Generating case secret/$1..."
  execmd=${programs[$2]}
  $($execmd ${@:3} $SEED > secret/$1.in)

  echo "Solving case secret/$1..."
  solve secret/$1
  cases[$1]="yes"
}

# Include all testcases in another group
# Arguments: group name to include
include_group () {
  for x in ${groups[$1]}
  do
    tc $x
  done
}

generate_grader() {
  mkdir -p $PPATH/graders
  python3 ../../testdata_tools/generate_grader.py > $PPATH/graders/grader.py
  rm cases groups
}
