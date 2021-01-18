from .TokenType import *

__all__ = ["Token"]

class Token(object):
  __slots__ = ("col","lexeme", "literal", "kind", "row")
    
  def __init__(self, kind : TokenType, lexeme : str, literal : object, 
																	row : int = 1, col : int = 0) :
    self.kind = kind
    self.lexeme = lexeme
    self.literal = literal
    self.row = row
    self.col = col

  def __str__(self) -> str:
    return str(self.kind) + " '" + self.lexeme + "'"
    
