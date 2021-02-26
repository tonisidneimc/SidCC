
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
    print("\tpushq %rbp")
    print("\tmovq %rsp, %rbp")
    
    if prog.stack_size != 0:
      prog.stack_size = cls._align_to(prog.stack_size, 16)
      print("\tsubq $%d, %%rsp" %(prog.stack_size))

    cls._gen_stmt(prog.body)
    assert(cls._depth == 0)   

    print(".L.return:")
    # Epilogue
    print("\tleave") # movq %rbp, %rsp; popq %rbp
    print("\tret")

  @classmethod
  def _push(cls) -> None:
    
    print("\tpushq %rax")
    cls._depth += 1

  @classmethod
  def _pop(cls, dest_reg : str) -> None:
    
    print("\tpopq %s" %(dest_reg))
    cls._depth -= 1

  @staticmethod
  def _align_to(n : int, align : int) -> int: 
    # round up n to the nearest multiple of align
    # if n = 11 and align = 8, then it rounds to 16
    # if n = 32 and align = 16, then n is aligned and it rounds to n
    return int((n + align - 1) / align) * align

  @classmethod
  def _gen_stmt(cls, stmt : Stmt) -> None:

    if isinstance(stmt, Block):
      for statement in stmt.body:
        cls._gen_stmt(statement)

    elif isinstance(stmt, Expression):
      if stmt.expression is not None:
        cls._gen_expr(stmt.expression)
    
    elif isinstance(stmt, Return):
      if stmt.ret_value is not None:
        cls._gen_expr(stmt.ret_value)
      print("\tjmp .L.return")


  @classmethod
  def _gen_addr(cls, var_desc : Obj) -> None:
   
    print("\tleaq %d(%%rbp), %%rax" %(var_desc.offset))
    return

  @classmethod
  def _gen_expr(cls, node : Expr):

    if isinstance(node, Literal):
      print("\tmovq $%d, %%rax" %(node.value))
      return

    if isinstance(node, Variable):
      cls._gen_addr(node.desc)
      print("\tmovq (%rax), %rax")
      return

    if isinstance(node, Assign):
      cls._gen_addr(node.lhs.desc)
      cls._push()      # pushq %rax
      cls._gen_expr(node.value)
      cls._pop("%rdi") # popq %rdi
      print("\tmovq %rax, (%rdi)")
      return

    if isinstance(node, Unary):
      if node.op.kind == TokenType.MINUS :
        cls._gen_expr(node.lhs)
        print("\tnegq %rax") 
        return  

    cls._gen_expr(node.rhs)
    cls._push()      # pushq %rax
    cls._gen_expr(node.lhs)
    cls._pop("%rdi") # popq %rdi

    if isinstance(node, Relational) :
      print("\tcmpq %rdi, %rax")

      if node.op.kind == TokenType.EQUAL_EQUAL:
        print("\tsete %al")
      elif node.op.kind == TokenType.BANG_EQUAL:
        print("\tsetne %al")
      elif node.op.kind in {TokenType.LESS, TokenType.GREATER}:
        print("\tsetl %al")
      elif node.op.kind in {TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL}:
        print("\tsetle %al")

      print("\tmovzbq %al, %rax"); return

    if isinstance(node, Binary) :
      if node.op.kind == TokenType.PLUS:
        print("\taddq %rdi, %rax")
      elif node.op.kind == TokenType.MINUS:
        print("\tsubq %rdi, %rax")
      elif node.op.kind == TokenType.STAR:
        print("\timulq %rdi, %rax")
      elif node.op.kind == TokenType.SLASH:
        print("\tcqto") # extends signal %rax -> %rdx     
        print("\tidivq %rdi")

