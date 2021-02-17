
from .expr import *

class Stmt(object) : pass

class Expression(Stmt) :
  def __init__(self, expr : Expr) :
    self.expression = expr


