import sys

if __name__ == "__main__" :

  if len(sys.argv) > 2 :
    sys.stderr.write("%s: invalid number of arguments" %(sys.argv[0]))
    sys.exit(64)
  
  print("""
  .text
    .globl main
  main:
    pushq %%rbp
    movq %%rsp, %%rbp
    movq $%d, %%rax
    leave
    ret""" %(int(sys.argv[1])))


