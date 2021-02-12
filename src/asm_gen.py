
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
    else :
      print("\t\tmovq $0, %rax")

    print("\t\tleave")
    print("\t\tret")

  def _gen_asm(self, node : Expr):

    if isinstance(node, Literal):
      print("\t\tmovq $%d, %%rax" %(node.value))
      return

    if isinstance(node, Unary):
      if node.op.kind == TokenType.MINUS :
        self._gen_asm(node.lhs)
        print("\t\tnegq %rax") 
        return    

    self._gen_asm(node.rhs)
    
    print("\t\tpushq %rax")
    
    self._gen_asm(node.lhs)
    
    print("\t\tpopq %rdi")

    if isinstance(node, Relational) :
      print("\t\tcmpq %rdi, %rax")

      if node.op.kind == TokenType.EQUAL_EQUAL:
        print("\t\tsete %al")
      elif node.op.kind == TokenType.BANG_EQUAL:
        print("\t\tsetne %al")
      elif node.op.kind in {TokenType.LESS, TokenType.GREATER}:
        print("\t\tsetl %al")
      elif node.op.kind in {TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL}:
        print("\t\tsetle %al")

      print("\t\tmovzbq %al, %rax"); return

    if isinstance(node, Binary) :
      if node.op.kind == TokenType.PLUS:
        print("\t\taddq %rdi, %rax")
      elif node.op.kind == TokenType.MINUS:
        print("\t\tsubq %rdi, %rax")
      elif node.op.kind == TokenType.STAR:
        print("\t\timulq %rdi, %rax")
      elif node.op.kind == TokenType.SLASH:
        print("\t\tcqto") # extends signal %rax -> %rdx     
        print("\t\tidivq %rdi")

