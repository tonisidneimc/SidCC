
from .expr import *

class Stmt(object) :
  def __init__(self) : pass
  
  @property
  def is_compound_stmt(self) -> bool:
    return isinstance(self, CompoundStmt)

  @property
  def is_expression_stmt(self) -> bool:
    return isinstance(self, ExpressionStmt)

  @property
  def is_return_stmt(self) -> bool:
    return isinstance(self, ReturnStmt)

  @property
  def is_if_stmt(self) -> bool:
    return isinstance(self, IfStmt)

  @property
  def is_for_stmt(self) -> bool:
    return isinstance(self, ForStmt)

  @property
  def is_function(self) -> bool:
    return isinstance(self, FunctionStmt)

class ExpressionStmt(Stmt) :
  def __init__(self, expr : Expr) :
    self.expression = expr

class ReturnStmt(Stmt) :
  def __init__(self, value : Expr) :
    self.ret_value = value

class CompoundStmt(Stmt) :
  def __init__(self, statements : list) :
    self.body = statements

class FunctionStmt(Stmt) : # function declaration as statement for now 
  def __init__(self, lvars : map, body : CompoundStmt, stack_size : int = 0) :
    self.body = body
    self.stack_size = stack_size
    self.lvars = lvars

class IfStmt(Stmt) :
  def __init__(self, condition : Expr, then_branch : Stmt, else_branch : Stmt) :
    self.condition = condition
    self.then_branch = then_branch
    self.else_branch = else_branch

class ForStmt(Stmt) :
  def __init__(self, init : Stmt, cond : Expr, inc : Expr, body : Stmt) :
    self.init = init
    self.condition = cond
    self.body = body
    self.inc = inc


