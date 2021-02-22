
from .token_type import *
from .stmt import *
from .expr import *
from .parser import Obj

class Asm_Generator :
  def __init__(self) : 
    self._depth = 0

  def gen(self, prog : Function) -> None: 
   
    print(".text")
    print("\t.globl main")
    print("\tmain:")
   
    # Prologue
    print("\t\tpushq %rbp")
    print("\t\tmovq %rsp, %rbp")
    
    if prog.stack_size != 0:
      prog.stack_size = self._align_to(prog.stack_size, 16)
      print("\t\tsubq $%d, %%rsp" %(prog.stack_size))

    for stmt in prog.body:
      self._gen_stmt(stmt)
      assert(self._depth == 0)    

    # Epilogue
    print("\t\tleave") # movq %rbp, %rsp; popq %rbp
    print("\t\tret")

  def _push(self) -> None:
    
    print("\t\tpushq %rax")
    self._depth += 1

  def _pop(self, dest_reg : str) -> None:
    
    print("\t\tpopq %s" %(dest_reg))
    self._depth -= 1

  def _align_to(self, n : int, align : int) -> int: 
    # round up n to the nearest multiple of align
    # if n = 11 and align = 8, then it rounds to 16
    # if n = 32 and align = 16, then n is aligned and it rounds to n
    return int((n + align - 1) / align) * align

  def _gen_stmt(self, stmt : Stmt) -> None:
    
    if isinstance(stmt, Expression):
      self._gen_expr(stmt.expression)

  def _gen_addr(self, var_desc : Obj) -> None:
   
    print("\t\tleaq %d(%%rbp), %%rax" %(var_desc.offset))
    return

  def _gen_expr(self, node : Expr):

    if isinstance(node, Literal):
      print("\t\tmovq $%d, %%rax" %(node.value))
      return

    if isinstance(node, Variable):
      self._gen_addr(node.desc)
      print("\t\tmovq (%rax), %rax")
      return

    if isinstance(node, Assign):
      self._gen_addr(node.lhs.desc)
      self._push()      # pushq %rax
      self._gen_expr(node.value)
      self._pop("%rdi") # popq %rdi
      print("\t\tmovq %rax, (%rdi)")
      return

    if isinstance(node, Unary):
      if node.op.kind == TokenType.MINUS :
        self._gen_expr(node.lhs)
        print("\t\tnegq %rax") 
        return  

    self._gen_expr(node.rhs)
    self._push()      # pushq %rax
    self._gen_expr(node.lhs)
    self._pop("%rdi") # popq %rdi

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

