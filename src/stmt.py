
from .expr import *

class Stmt(object) : pass

class Expression(Stmt) :
  def __init__(self, expr : Expr) :
    self.expression = expr

class Return(Stmt) :
  def __init__(self, value : Expr) :
    self.ret_value = value

class Block(Stmt) :
  def __init__(self, statements : list) :
    self.body = statements

class Function(Stmt) :
  def __init__(self, lvars : map, body : Block, stack_size : int = 0) :
    self.body = body
    self.stack_size = stack_size
    self.lvars = lvars

class If(Stmt) :
  def __init__(self, condition : Expr, then_branch : Stmt, else_branch : Stmt) :
    self.condition = condition
    self.then_branch = then_branch
    self.else_branch = else_branch

class For(Stmt) :
  def __init__(self, init : Stmt, cond : Expr, inc : Expr, body : Stmt) :
    self.init = init
    self.condition = cond
    self.body = body
    self.inc = inc


