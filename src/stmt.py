
from .expr import *

class Stmt(object) : pass

class Expression(Stmt) :
  def __init__(self, expr : Expr) :
    self.expression = expr

class Function(Stmt) :
  def __init__(self, lvars : map, body : list, stack_size : int = 0) :
    self.body = body
    self.stack_size = stack_size
    self.lvars = lvars

