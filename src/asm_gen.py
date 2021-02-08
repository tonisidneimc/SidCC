
from .token_type import *
from .expr import *

class Asm_Generator :
  def __init__(self, stmts : list) :
    self.stmts = stmts
  
  def gen(self) :
    
    print(".text")
    print("\t.globl main")
    print("\tmain:")
    print("\t\tpushq %rbp")
    print("\t\tmovq %rsp, %rbp")

    if self.stmts != [] :
      for ast in self.stmts:
        self._gen_asm(ast)
      print("\t\tpopq %rax")    
    else :
      print("\t\tmovq $0, %rax")

    print("\t\tleave")
    print("\t\tret")

  def _gen_asm(self, node : Expr):

    if isinstance(node, Literal):
      print("\t\tpushq $%d" %(node.value))
      return

    if isinstance(node, Unary):
      if node.op.kind == TokenType.MINUS :
        self._gen_asm(node.lhs)
        print("\t\tpopq %rax")
        print("\t\tnegq %rax")
        print("\t\tpushq %rax") 
        return    

    self._gen_asm(node.lhs)
    self._gen_asm(node.rhs)

    print("\t\tpopq %rdi")
    print("\t\tpopq %rax")

    if node.op.kind == TokenType.PLUS:
      print("\t\taddq %rdi, %rax")
    elif node.op.kind == TokenType.MINUS:
      print("\t\tsubq %rdi, %rax")
    elif node.op.kind == TokenType.STAR:
      print("\t\timulq %rdi, %rax")
    elif node.op.kind == TokenType.SLASH:
      print("\t\tcqto") # extends signal %rax -> %rdx     
      print("\t\tidivq %rdi")

    print("\t\tpushq %rax")

    
