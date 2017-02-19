set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

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
# Arguments: file opts
compile_cpp () {
  if [[ $2 == *"opt"* ]]; then
    g++ -O2 -Wall -std=gnu++11 -o $(base $1) $1
  else
    g++ -O2 -fsanitize=undefined -fsanitize=address -Wall -std=gnu++11 -o $(base $1) $1
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

setup_dirs () {
  rm -rf groups cases secret
  mkdir -p secret
  echo "grading: custom
grader_flags: ignore" > sample/testdata.yaml
  echo "grading: custom
grader_flags: groups" > secret/testdata.yaml
  echo "grading: custom
grader_flags: sum" > testdata.yaml
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
  rm -rf *.class
  rm cases groups
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
  if [[ ${cases[$1]} != $CURGROUP ]]; then
    groups[$CURGROUP_NAME]="${groups[$CURGROUP_NAME]} $1"
    echo $1 $CURGROUP >> cases
  fi
  if [[ ${cases[$1]} != "" ]]
  then
    if [[ $# == 1 ]]; then
      if [[ ${cases[$1]} == $CURGROUP ]]; then
        echo "Skipping duplicate case secret/$1"
      else
        cases[$1]=$CURGROUP
        echo "Reusing secret/$1"
      fi
      return 0
    else
      echo "ERROR: duplicate test case name $1"
      exit 1
    fi
  fi
  SEED=$(( SEED+1 ))
  echo "Generating case secret/$1..."
  execmd=${programs[$2]}
  $($execmd "${@:3}" $SEED > secret/$1.in)

  echo "Solving case secret/$1..."
  solve secret/$1
  cases[$1]=$CURGROUP
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
  python3 "$DIR/generate_grader.py" > $PPATH/graders/grader.py
}

generate_cms() {
  python3 "$DIR/generate_cms.py" > $PPATH/data/cms
}
