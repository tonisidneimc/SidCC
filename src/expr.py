from .token import *
from .token_type import *

class Expr(object) :
  
  operand_type = None

  @property
  def is_unary(self) -> bool:
    return isinstance(self, UnaryExpr)

  @property
  def is_binary(self) -> bool:
    return isinstance(self, BinaryExpr)

  @property
  def is_literal(self) -> bool:
    return isinstance(self, LiteralExpr)

  @property
  def is_variable(self) -> bool:
    return isinstance(self, VariableExpr)

  @property
  def is_assignment(self) -> bool:
    return isinstance(self, AssignExpr)

  @property
  def is_funcall(self) -> bool:
    return isinstance(self, FunCallExpr)

class UnaryExpr (Expr) :
  def __init__(self, lhs : Expr, operator : Token) :
    self.op = operator
    self.lhs = lhs

  @property
  def is_neg(self) -> bool:
    return self.op.kind == TokenType.MINUS

  @property
  def is_addressing(self) -> bool: 
    return self.op.kind == TokenType.AMPERSAND

  @property
  def is_deref(self) -> bool:
    return self.op.kind == TokenType.STAR
	
class BinaryExpr (Expr) :
  def __init__(self, lhs : Expr, operator : Token, rhs : Expr) :
    self.lhs = lhs
    self.op = operator
    self.rhs = rhs

  @property
  def is_cmp_eq(self) -> bool: 
    return self.op.kind == TokenType.EQUAL_EQUAL

  @property
  def is_cmp_ne(self) -> bool: 
    return self.op.kind == TokenType.BANG_EQUAL

  @property
  def is_cmp_less(self) -> bool: 
    return self.op.kind == TokenType.LESS or \
           self.op.kind == TokenType.GREATER

  @property
  def is_cmp_leq(self) -> bool:
    return self.op.kind == TokenType.LESS_EQUAL or \
           self.op.kind == TokenType.GREATER_EQUAL

  @property
  def is_relational(self) -> bool:
    return self.is_cmp_eq or self.is_cmp_ne or \
           self.is_cmp_less or self.is_cmp_leq

  @property
  def is_add(self) -> bool: 
    return self.op.kind == TokenType.PLUS

  @property
  def is_sub(self) -> bool: 
    return self.op.kind == TokenType.MINUS

  @property
  def is_mul(self) -> bool: 
    return self.op.kind == TokenType.STAR

  @property
  def is_div(self) -> bool: 
    return self.op.kind == TokenType.SLASH

  @property
  def is_arithmetic(self) -> bool:
    return self.is_add or self.is_sub or \
           self.is_mul or self.is_div


class LiteralExpr (Expr) :
  def __init__(self, value : int) :
    self.value = value

class VariableExpr (Expr) :
  def __init__(self, name : str, var_desc : object) :
    self.var_desc = var_desc
    self.name = name

class AssignExpr (Expr) :
  def __init__(self, expr : Expr, equals : Token, value : Expr) :
    self.lhs = expr
    self.equals = equals
    self.value = value

class FunCallExpr (Expr) :
  def __init__(self, callee : str, args : list = []) :
    self.callee = callee
    self.args = args


