from .token_type import *

__all__ = ["Token"]

_debug = {
  TokenType.SEMICOLON : "SEMICOLON",
  TokenType.LEFT_PAREN : "LEFT_PAREN", 
  TokenType.RIGHT_PAREN : "RIGHT_PAREN",
  TokenType.LEFT_BRACE : "LEFT_BRACE",
  TokenType.RIGHT_BRACE : "RIGHT_BRACE",
  TokenType.LEFT_BRACKET : "LEFT_BRACKET",
  TokenType.RIGHT_BRACKET : "RIGHT_BRACKET",
  TokenType.AMPERSAND : "AMPERSAND", 
  TokenType.PLUS : "PLUS",
  TokenType.MINUS : "MINUS",
  TokenType.SLASH : "SLASH",
  TokenType.STAR : "STAR",
  TokenType.EQUAL : "EQUAL",
  TokenType.BANG : "BANG",
  TokenType.LESS : "LESS",
  TokenType.GREATER : "GREATER",
  TokenType.EQUAL_EQUAL : "EQUAL_EQUAL",
  TokenType.BANG_EQUAL : "BANG_EQUAL",
  TokenType.LESS_EQUAL : "LESS_EQUAL",
  TokenType.GREATER_EQUAL : "GREATER_EQUAL",
  TokenType.IDENTIFIER : "IDENTIFIER",
  TokenType.IF : "IF",
  TokenType.ELSE : "ELSE",
  TokenType.FOR : "FOR",
  TokenType.WHILE : "WHILE",
  TokenType.RETURN : "RETURN",
  TokenType.NUM : "NUM",
  TokenType.EOF : "EOF"
}

class Token(object):
    
  def __init__(self, kind : TokenType, lexeme : str, literal : object, 
                                          row : int = 1, col : int = 0) :
    self.kind = kind
    self.lexeme = lexeme
    self.literal = literal
    self.row = row
    self.col = col

  def __str__(self) -> str:

    token_kind = _debug[self.kind]

    return "{:<14s} -> \'{:<}\'".format(token_kind, self.lexeme)

  def __copy__(self) :

    result = type(self).__new__(self.__class__)
    result.__dict__.update(self.__dict__)
    return result

