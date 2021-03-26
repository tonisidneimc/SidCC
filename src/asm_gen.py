
from .stmt import *
from .expr import *
from .parser import Object
from .data_type import *

class Asm_Generator :
  
  _depth = 0
  _label_count = 0
  _argreg = ["%rdi", "%rsi", "%rdx", "%rcx", "%r8", "%r9"]
  _curr_funct = None

  @classmethod
  def gen(cls, prog : list) -> None:

    print(".text")

    for fn in prog :

      print("\t.globl %s" %(fn.name))
      print("%s:" %(fn.name))
      
      cls._curr_funct = fn

      # Prologue
      print("\tpushq %rbp")
      print("\tmovq %rsp, %rbp")
    
      if fn.stack_size != 0:
        fn.stack_size = cls._align_to(fn.stack_size, 16)
        print("\tsubq $%d, %%rsp" %(fn.stack_size))

      # save passed-by-register arguments to the stack
      for reg, var in zip(cls._argreg, fn.params) :
        print("\tmovq %s, %d(%%rbp)" %(reg, var.offset))

      # emit code
      cls._gen_stmt(fn.body)
      assert(cls._depth == 0)
   
      print(".L.return.%s:" %(fn.name))
      # Epilogue
      print("\tleave") # movq %rbp, %rsp; popq %rbp
      print("\tret\n")

  @classmethod
  def _request_label(cls) -> int:
    cls._label_count += 1
    return cls._label_count

  @classmethod
  def _push(cls) -> None:
    
    print("\tpushq %rax")
    cls._depth += 1

  @classmethod
  def _pop(cls, dest_reg : str) -> None:
    
    print("\tpopq %s" %(dest_reg))
    cls._depth -= 1

  @classmethod
  def _load(cls, data_type : DataType) -> None:
  
    if data_type.is_array:
      # cannot load an entire array into a register
      # so the register will contain only a reference to the first element in the array
      # this is the expected behaviour in C
      # this reference is already in the register, so it returns
      return
    else:
      print("\tmovq (%rax), %rax")

  @classmethod
  def _store(cls) -> None:
    # store %rax into the address pointed by %rdi 
    cls._pop("%rdi")
    print("\tmovq %rax, (%rdi)")

  @staticmethod
  def _align_to(n : int, align : int) -> int: 
    # round up n to the nearest multiple of align
    # if n = 11 and align = 8, then it rounds to 16
    # if n = 32 and align = 16, then n is aligned and it rounds to n
    return int((n + align - 1) / align) * align

  @classmethod
  def _gen_stmt(cls, stmt : Stmt) -> None:

    if stmt.is_if_stmt:
      lc = cls._request_label()
      
      cls._gen_expr(stmt.condition)
      print("\tcmpq $0, %rax")
      print("\tje .L.else.%d" %(lc))
      
      cls._gen_stmt(stmt.then_branch)
      print("\tjmp .L.end.%d" %(lc))
      
      print(".L.else.%d:" %(lc))
      if stmt.else_branch is not None:
        cls._gen_stmt(stmt.else_branch)
      
      print(".L.end.%d:" %(lc))

    elif stmt.is_for_stmt:
      lc = cls._request_label()

      if stmt.init is not None: 
        cls._gen_stmt(stmt.init)
      
      print(".L.begin.%d:" %(lc))
      if stmt.condition is not None:
        cls._gen_expr(stmt.condition)
        print("\tcmpq $0, %rax")
        print("\tje .L.end.%d" %(lc))

      cls._gen_stmt(stmt.body)
      
      if stmt.inc is not None:
        cls._gen_expr(stmt.inc)

      print("\tjmp .L.begin.%d" %(lc))
      print(".L.end.%d:" %(lc))

    elif stmt.is_compound_stmt:
      for statement in stmt.body:
        cls._gen_stmt(statement)

    elif stmt.is_expression_stmt:
      if stmt.expression is not None:
        cls._gen_expr(stmt.expression)
    
    elif stmt.is_return_stmt:
      if stmt.ret_value is not None:
        cls._gen_expr(stmt.ret_value)
      print("\tjmp .L.return.%s" %(cls._curr_funct.name))

  @classmethod
  def _gen_addr(cls, node : Expr) -> None:
    
    if node.is_variable:
      print("\tleaq %d(%%rbp), %%rax" %(node.var_desc.offset))
      return
    
    elif node.is_unary and node.is_deref:
      # dereference expression
      cls._gen_expr(node.lhs)
      return

  @classmethod
  def _gen_expr_unary(cls, node : Expr) -> None:  

    assert(node.is_unary) # security check only  

    if node.is_addressing :
      # address_of expression 
      cls._gen_addr(node.lhs)
      return
    else:
      cls._gen_expr(node.lhs)

      if node.is_neg:
        # negate expression
        print("\tnegq %rax") 
        return

      elif node.is_deref:
        # dereference expression
        cls._load(node.operand_type)
        return    

  @classmethod
  def _gen_expr_binary(cls, node : Expr) -> None:

    assert(node.is_binary) # security check only

    cls._gen_expr(node.rhs)
    cls._push()      # pushq %rax
    cls._gen_expr(node.lhs)
    cls._pop("%rdi") # popq %rdi

    if node.is_add:
      print("\taddq %rdi, %rax")
    
    elif node.is_sub:
      print("\tsubq %rdi, %rax")
    
    elif node.is_mul:
      print("\timulq %rdi, %rax")
    
    elif node.is_div:
      print("\tcqto") # extends signal %rax -> %rdx     
      print("\tidivq %rdi")
    
    else: # relational expression
      print("\tcmpq %rdi, %rax")

      if node.is_cmp_eq:
        print("\tsete %al")
      
      elif node.is_cmp_ne:
        print("\tsetne %al")
      
      elif node.is_cmp_less:
        print("\tsetl %al")
      
      elif node.is_cmp_leq:
        print("\tsetle %al")

      print("\tmovzbq %al, %rax")

  @classmethod
  def _gen_expr(cls, node : Expr) -> None:

    if node.is_literal:
      print("\tmovq $%d, %%rax" %(node.value))
      return

    elif node.is_variable:
      cls._gen_addr(node)
      cls._load(node.operand_type)
      return

    elif node.is_funcall:
      
      nargs = len(node.args)

      for arg in node.args :
        cls._gen_expr(arg) # gen expression to %rax
        cls._push()        # pushq %rax

      if nargs != 0 :
        for reg in cls._argreg[nargs-1::-1] :
          cls._pop(reg) # popq to arg register     

      print("\tmovq $0, %rax")
      print("\tcall %s" %(node.callee))
      return

    elif node.is_assignment:
      cls._gen_addr(node.lhs)
      cls._push()      # pushq %rax
      cls._gen_expr(node.value)
      cls._store()
      return

    elif node.is_unary:
      cls._gen_expr_unary(node)
      
    elif node.is_binary:
      cls._gen_expr_binary(node)


