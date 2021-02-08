from .token import *

class Expr(object) : pass

class Literal (Expr) :
  def __init__(self, value : int) :
    self.value = value
	
class Binary (Expr) :
  def __init__(self, lhs : Expr, operator : Token, rhs : Expr) :
    self.lhs = lhs
    self.op = operator
    self.rhs = rhs

class Unary (Expr) :
  def __init__(self, lhs : Expr, operator : Token) :
    self.lhs = lhs
    self.op = operator


