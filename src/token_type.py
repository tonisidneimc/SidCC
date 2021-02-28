__all__ = ["TokenType"]

class TokenType :
  SEMICOLON, \
  \
  LEFT_PAREN, RIGHT_PAREN, LEFT_BRACE, RIGHT_BRACE, \
  \
  PLUS, MINUS, SLASH, STAR, \
  \
  BANG, BANG_EQUAL, EQUAL, EQUAL_EQUAL, \
  GREATER, GREATER_EQUAL, LESS, LESS_EQUAL, \
  \
  IDENTIFIER, NUM, \
  \
  ELSE, IF, RETURN, \
  \
  EOF =  range(23)


