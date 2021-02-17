
from .token_type import *
from .stmt import *
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
    print("\t\tsubq $208, %rsp") # 8 * 26 letters for local variables

    for stmt in self.stmts:
      self._gen_stmt(stmt)
    
    print("\t\tleave")
    print("\t\tret")

  def _gen_stmt(self, stmt : Stmt) -> None:
    
    if isinstance(stmt, Expression):
      self._gen_expr(stmt.expression)

  def _gen_addr(self, var_name : str) -> None:
   
    offset = int((ord(var_name) - 96) * 8)
    print("\t\tleaq %d(%%rbp), %%rax" %(-offset))
    return

  def _gen_expr(self, node : Expr):

    if isinstance(node, Literal):
      print("\t\tmovq $%d, %%rax" %(node.value))
      return

    if isinstance(node, Variable):
      self._gen_addr(node.name)
      print("\t\tmovq (%rax), %rax")
      return

    if isinstance(node, Assign):
      self._gen_addr(node.lhs.name)
      print("\t\tpushq %rax")
      
      self._gen_expr(node.value)
      
      print("\t\tpopq %rdi")
      print("\t\tmovq %rax, (%rdi)")
      return

    if isinstance(node, Unary):
      if node.op.kind == TokenType.MINUS :
        self._gen_expr(node.lhs)
        print("\t\tnegq %rax") 
        return  

    self._gen_expr(node.rhs)
    
    print("\t\tpushq %rax")
    
    self._gen_expr(node.lhs)
    
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

