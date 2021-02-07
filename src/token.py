from .token_type import *

__all__ = ["Token"]

_debug = {
  TokenType.LEFT_PAREN : "LEFT_PAREN", 
  TokenType.RIGHT_PAREN : "RIGHT_PAREN", 
  TokenType.PLUS : "PLUS",
  TokenType.MINUS : "MINUS",
  TokenType.SLASH : "SLASH",
  TokenType.STAR : "STAR",
  TokenType.NUM : "NUM",
  TokenType.EOF : "EOF"
}

class Token(object):
  __slots__ = ("col", "lexeme", "literal", "kind", "row")
    
  def __init__(self, kind : TokenType, lexeme : str, literal : object, row : int = 1, col : int = 0) :
    self.kind = kind
    self.lexeme = lexeme
    self.literal = literal
    self.row = row
    self.col = col

  def __str__(self) -> str:

    return _debug[self.kind] + " '" + self.lexeme + "'"
    
