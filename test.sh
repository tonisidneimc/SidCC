#!/bin/bash

function assert {
  expected=$1
  input=$2
  
  python3 main.py "$input" > tmp.S
  gcc -o tmp tmp.S
  ./tmp
  actual=$?

  if [ "$actual" = "$expected" ]; then
    echo "$input => $actual"
  else
    echo "$input => expected $expected, got $actual"
    exit 1
  fi
}

assert 0 0 
assert 42 42
assert 21 '5+20-4'
assert 41 ' 12 + 34 - 5 '
assert 47 '5+6*7'
assert 15 '5*(9-6)'
assert 4 '(3+5)/2'
assert 10 '-10+20'
assert 10 '- -10'
assert 10 '- - +10'
assert 22 '-(5*-3) + 7'
assert 15 '-(-(-9/-3)-12)'

echo OK
