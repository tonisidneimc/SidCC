#!/bin/bash

# cat input until EOF keyword and use it as a pipe to gcc
# gcc compile as a .c source file, but stops before linking
cat <<EOF | gcc -xc -c -o tmp2.o -
int ret2() { return 2; }
int ret8() { return 8; }
int add(int x, int y) { return x+y; }
int sub(int x, int y) { return x-y; }
int add6(int a, int b, int c, int d, int e, int f) { return a+b+c+d+e+f; }
EOF

function assert {
  expected=$1
  input=$2
  
  python3 main.py "$input" > tmp.S  2>STDERR.txt
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

assert 0  'int main() { return 0; }' 
assert 42 'int main() { return 42; }'
assert 21 'int main() { return 5+20-4; }'
assert 41 'int main() { return 12 + 34 - 5 ; }'
assert 47 'int main() { return 5+6*7; }'
assert 15 'int main() { return 5*(9-6); }'
assert 4  'int main() { return (3+5)/2; }'

assert 10 'int main() { return -10+20; }'
assert 10 'int main() { return - -10; }'
assert 10 'int main() { return - - +10; }'
assert 22 'int main() { return -(5*-3) + 7; }'
assert 15 'int main() { return -(-(-9/-3)-12); }'

assert 0 'int main() { return 0==1; }'
assert 1 'int main() { return 42==42; }'
assert 1 'int main() { return 0!=1; }'
assert 0 'int main() { return 42!=42; }'

assert 1 'int main() { return 0<1; }'
assert 0 'int main() { return 1<1; }'
assert 0 'int main() { return 2<1; }'
assert 1 'int main() { return 0<=1; }'
assert 1 'int main() { return 1<=1; }'
assert 0 'int main() { return 2<=1; }'

assert 1 'int main() { return 1>0; }'
assert 0 'int main() { return 1>1; }'
assert 0 'int main() { return 1>2; }'
assert 1 'int main() { return 1>=0; }'
assert 1 'int main() { return 1>=1; }'
assert 0 'int main() { return 1>=2; }'

assert 3 'int main() { int a=3; return a; }'
assert 4 'int main() { int a=3, b=2, c=1; return a+b-c; }'
assert 6 'int main() { int a, b; a=b=3; return a+b; }'

assert 3 'int main() { int foo=3; return foo; }'
assert 8 'int main() { int _foo_123=3; int bar=5; return _foo_123+bar; }'

assert 1 'int main() { return 1; 2; 3; }'
assert 2 'int main() { 1; return 2; 3; }'
assert 3 'int main() { 1; 2; return 3; }' 

assert 3 'int main() { {1; {2;} return 3;} }'
assert 5 'int main() { ;;; return 5; }'

assert 3 'int main() { if (0) return 2; return 3; }'
assert 3 'int main() { if (1-1) return 2; return 3; }'
assert 2 'int main() { if (1) return 2; return 3; }'
assert 2 'int main() { if (2-1) return 2; return 3; }'
assert 4 'int main() { if (0) { 1; 2; return 3; } else { return 4; } }'
assert 3 'int main() { if (1) { 1; 2; return 3; } else { return 4; } }'

assert 2 'int main() { int a=3, b=2; if(a<=b) return a; else return b;}'
assert 3 'int main() { int a=3, b=2; if(a>b) return a; else return b;}'

assert 55 'int main() { int i=0, j=0; for (i=0; i<=10; i=i+1) j=i+j; return j; }'
assert  3 'int main() { for (;;) {return 3;} return 5; }'

assert 10 'int main() { int i=0; while(i<10) { i=i+1; } return i; }'

assert 3 'int main() { int x=3; return *&x; }'
assert 3 'int main() { int x=3; int* y=&x; int** z=&y; return **z; }'
assert 5 'int main() { int x=3, y=5; return *(&x-1); }'
assert 3 'int main() { int x=3, y=5; return *(&y+1); }'
assert 5 'int main() { int x=3; int* y=&x; *y=5; return x; }'
assert 7 'int main() { int x=3, y=5; *(&x-1)=7; return y; }'
assert 7 'int main() { int x=3, y=5; *(&y+1)=7; return x; }'

assert 3 'int main() { int x=3, y=5; return *(&y-(-1));}'
assert 7 'int main() { int x=3, y=5; *(&x-1)=7; return y; }'
assert 7 'int main() { int x=3, y=5; *(&y+2-1)=7; return x; }'
assert 5 'int main() { int x=3; return (&x+2)-&x+3; }'

assert   2 'int main() { return ret2(); }'
assert   7 'int main() { return 5 + ret2(); }'
assert  10 'int main() { return ret2() + ret8(); }'
assert   8 'int main() { return add(3, 5); }'
assert   2 'int main() { return sub(5, 3); }'
assert  21 'int main() { return add6(1,2,3,4,5,6); }'
assert  66 'int main() { return add6(1,2,add6(3,4,5,6,7,8),9,10,11); }'
assert 136 'int main() { return add6(1,2,add6(3,add6(4,5,6,7,8,9),10,11,12,13),14,15,16); }'

assert 32 'int main() { return ret32(); } int ret32() { return 32; }'
assert  7 'int main() { return add2(3,4); } int add2(int x, int y) { return x+y; }'
assert  1 'int main() { return sub2(4,3); } int sub2(int x, int y) { return x-y; }'
assert 55 'int main() { return fib(9); } int fib(int x) { if (x<=1) return 1; return fib(x-1) + fib(x-2); }'

assert 3 'int main() { int x[2]; int* y=&x; *y=3; return *x; }'

assert 3 'int main() { int x[3]; *x=3; *(x+1)=4; *(x+2)=5; return *x; }'
assert 4 'int main() { int x[3]; *x=3; *(x+1)=4; *(x+2)=5; return *(x+1); }'
assert 5 'int main() { int x[3]; *x=3; *(x+1)=4; *(x+2)=5; return *(x+2); }'

echo OK
