#!/bin/bash

function assert {
  expected=$1
  input=$2
  
  python3 main.py $input > tmp.S
  gcc -o tmp tmp.S
  ./tmp
  actual=$?

  if [ $actual = $expected ]; then
    echo "$input => $actual"
  else
    echo "$input => expected $expected, got $actual"
    exit 1
  fi
}

assert 0 0 
assert 42 42

echo OK
