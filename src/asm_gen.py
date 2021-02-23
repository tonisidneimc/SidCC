
from .token_type import *
from .stmt import *
from .expr import *
from .parser import Obj

class Asm_Generator :
  
  _depth = 0

  @classmethod
  def gen(cls, prog : Function) -> None: 
   
    print(".text")
    print("\t.globl main")
    print("main:")
   
    # Prologue
    print("\t\tpushq %rbp")
    print("\t\tmovq %rsp, %rbp")
    
    if prog.stack_size != 0:
      prog.stack_size = cls._align_to(prog.stack_size, 16)
      print("\t\tsubq $%d, %%rsp" %(prog.stack_size))

    for stmt in prog.body:
      cls._gen_stmt(stmt)
      assert(cls._depth == 0)    

    # Epilogue
    print("\t\tleave") # movq %rbp, %rsp; popq %rbp
    print("\t\tret")

  @classmethod
  def _push(cls) -> None:
    
    print("\t\tpushq %rax")
    cls._depth += 1

  @classmethod
  def _pop(cls, dest_reg : str) -> None:
    
    print("\t\tpopq %s" %(dest_reg))
    cls._depth -= 1

  @staticmethod
  def _align_to(n : int, align : int) -> int: 
    # round up n to the nearest multiple of align
    # if n = 11 and align = 8, then it rounds to 16
    # if n = 32 and align = 16, then n is aligned and it rounds to n
    return int((n + align - 1) / align) * align

  @classmethod
  def _gen_stmt(cls, stmt : Stmt) -> None:
    
    if isinstance(stmt, Expression):
      cls._gen_expr(stmt.expression)
    
  @classmethod
  def _gen_addr(cls, var_desc : Obj) -> None:
   
    print("\t\tleaq %d(%%rbp), %%rax" %(var_desc.offset))
    return

  @classmethod
  def _gen_expr(cls, node : Expr):

    if isinstance(node, Literal):
      print("\t\tmovq $%d, %%rax" %(node.value))
      return

    if isinstance(node, Variable):
      cls._gen_addr(node.desc)
      print("\t\tmovq (%rax), %rax")
      return

    if isinstance(node, Assign):
      cls._gen_addr(node.lhs.desc)
      cls._push()      # pushq %rax
      cls._gen_expr(node.value)
      cls._pop("%rdi") # popq %rdi
      print("\t\tmovq %rax, (%rdi)")
      return

    if isinstance(node, Unary):
      if node.op.kind == TokenType.MINUS :
        cls._gen_expr(node.lhs)
        print("\t\tnegq %rax") 
        return  

    cls._gen_expr(node.rhs)
    cls._push()      # pushq %rax
    cls._gen_expr(node.lhs)
    cls._pop("%rdi") # popq %rdi

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

