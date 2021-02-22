from .token import *

class Expr(object) : pass

class Unary (Expr) :
  def __init__(self, lhs : Expr, operator : Token) :
    self.lhs = lhs
    self.op = operator
	
class Binary (Expr) :
  def __init__(self, lhs : Expr, operator : Token, rhs : Expr) :
    self.lhs = lhs
    self.op = operator
    self.rhs = rhs

class Relational (Binary) :
  def __init__(self, lhs : Expr, operator : Token, rhs : Expr) :
    super().__init__(lhs, operator, rhs)

class Literal (Expr) :
  def __init__(self, value : int) :
    self.value = value

class Variable (Expr) :
  def __init__(self, name : str, var_desc : object) :
    self.name = name
    self.desc = var_desc

class Assign (Expr) :
  def __init__(self, expr : Expr, value : Expr) :
    self.lhs = expr
    self.value = value

