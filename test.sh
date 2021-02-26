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

assert 0  '{ return 0; }' 
assert 42 '{ return 42; }'
assert 21 '{ return 5+20-4; }'
assert 41 '{ return 12 + 34 - 5 ; }'
assert 47 '{ return 5+6*7; }'
assert 15 '{ return 5*(9-6); }'
assert 4  '{ return (3+5)/2; }'

assert 10 '{ return -10+20; }'
assert 10 '{ return - -10; }'
assert 10 '{ return - - +10; }'
assert 22 '{ return -(5*-3) + 7; }'
assert 15 '{ return -(-(-9/-3)-12); }'

assert 0 '{ return 0==1; }'
assert 1 '{ return 42==42; }'
assert 1 '{ return 0!=1; }'
assert 0 '{ return 42!=42; }'

assert 1 '{ return 0<1; }'
assert 0 '{ return 1<1; }'
assert 0 '{ return 2<1; }'
assert 1 '{ return 0<=1; }'
assert 1 '{ return 1<=1; }'
assert 0 '{ return 2<=1; }'

assert 1 '{ return 1>0; }'
assert 0 '{ return 1>1; }'
assert 0 '{ return 1>2; }'
assert 1 '{ return 1>=0; }'
assert 1 '{ return 1>=1; }'
assert 0 '{ return 1>=2; }'

assert 3 '{ a=3; return a; }'
assert 4 '{ a=3; b=2; c=1; return a+b-c; }'
assert 6 '{ a=b=3; return a+b; }'

assert 3 '{ foo=3; return foo; }'
assert 8 '{ _foo_123=3; bar=5; return _foo_123+bar; }'

assert 1 '{ return 1; 2; 3; }'
assert 2 '{ 1; return 2; 3; }'
assert 3 '{ 1; 2; return 3; }' 

assert 3 '{ {1; {2;} return 3;} }'
assert 5 '{ ;;; return 5; }'

echo OK
