#!/bin/bash

# cat input until EOF keyword and use it as a pipe to gcc
# gcc compile as a .c source file, but stops before linking
cat <<EOF | gcc -xc -c -o tmp2.o -
int ret2() { return 2; }
int ret8() { return 8; }
EOF

function assert {
  expected=$1
  input=$2
  
  python3 main.py "$input" > tmp.S
  gcc -o tmp tmp.S tmp2.o
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

assert 3 '{ int a=3; return a; }'
assert 4 '{ int a=3, b=2, c=1; return a+b-c; }'
assert 6 '{ int a, b; a=b=3; return a+b; }'

assert 3 '{ int foo=3; return foo; }'
assert 8 '{ int _foo_123=3; int bar=5; return _foo_123+bar; }'

assert 1 '{ return 1; 2; 3; }'
assert 2 '{ 1; return 2; 3; }'
assert 3 '{ 1; 2; return 3; }' 

assert 3 '{ {1; {2;} return 3;} }'
assert 5 '{ ;;; return 5; }'

assert 3 '{ if (0) return 2; return 3; }'
assert 3 '{ if (1-1) return 2; return 3; }'
assert 2 '{ if (1) return 2; return 3; }'
assert 2 '{ if (2-1) return 2; return 3; }'
assert 4 '{ if (0) { 1; 2; return 3; } else { return 4; } }'
assert 3 '{ if (1) { 1; 2; return 3; } else { return 4; } }'

assert 2 '{ int a=3, b=2; if(a<=b) return a; else return b;}'
assert 3 '{ int a=3, b=2; if(a>b) return a; else return b;}'

assert 55 '{ int i=0, j=0; for (i=0; i<=10; i=i+1) j=i+j; return j; }'
assert 3 '{ for (;;) {return 3;} return 5; }'

assert 10 '{ int i=0; while(i<10) { i=i+1; } return i; }'

assert 3 '{ int x=3; return *&x; }'
assert 3 '{ int x=3; int* y=&x; int* z=&y; return **z; }'
assert 5 '{ int x=3, y=5; return *(&x-1); }'
assert 3 '{ int x=3, y=5; return *(&y+1); }'
assert 5 '{ int x=3; int* y=&x; *y=5; return x; }'
assert 7 '{ int x=3, y=5; *(&x-1)=7; return y; }'
assert 7 '{ int x=3, y=5; *(&y+1)=7; return x; }'

assert 3 '{ int x=3, y=5; return *(&y-(-1));}'
assert 7 '{ int x=3, y=5; *(&x-1)=7; return y; }'
assert 7 '{ int x=3, y=5; *(&y+2-1)=7; return x; }'
assert 5 '{ int x=3; return (&x+2)-&x+3; }'

assert 2 '{ return ret2(); }'
assert 7 '{ return 5 + ret2(); }'
assert 10 '{ return ret2() + ret8(); }'

echo OK
