__all__ = ["TokenType"]

class TokenType :
  LEFT_PAREN, RIGHT_PAREN, \
  \
  PLUS, MINUS, SLASH, STAR, \
  \
  BANG, BANG_EQUAL, EQUAL, EQUAL_EQUAL, \
  GREATER, GREATER_EQUAL, LESS, LESS_EQUAL, \
  \
  NUM, \
  \
  EOF =  range(16)


