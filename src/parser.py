
from .token import *
from .token_type import *
from .expr import *
from .errors import ParseError, error_collector

class Parser :
  
  def __init__(self, tokens : list) :
    self._current = 0
    self._tokens = tokens    

  def parse(self) -> list :
    statements = []
    
    while not self._is_at_end() :
      try:
        stmt = self._expression()

      except ParseError as err :
        error_collector.add(err); break
      else:
        statements.append(stmt)

    return statements

  def _expression(self) -> Expr:
    
    left = self._multiplication()
    
    while self._consume(TokenType.PLUS, TokenType.MINUS) :
      operator = self._previous()
      right = self._multiplication()
     
      left = Binary(left, operator, right)

    return left

  def _multiplication(self) -> Expr:

    left = self._unary()
        
    while self._consume(TokenType.SLASH, TokenType.STAR) :
      operator = self._previous()
      right = self._unary()
     
      left = Binary(left, operator, right)

    return left

  def _unary(self) -> Expr :
    
    if self._consume(TokenType.PLUS) :
      return self._unary()

    if self._consume(TokenType.MINUS) :
      operator = self._previous()
      left = self._unary()      

      return Unary(left, operator)

    return self._primary()

  def _primary(self) -> Expr:
    
    if self._consume(TokenType.NUM) :
      return Literal(self._previous().literal)

    elif self._consume(TokenType.LEFT_PAREN) :
      left = self._expression()
      self._expect(TokenType.RIGHT_PAREN, err_msg = "Expect ')' after expression")
      
      return left

    else :
      raise ParseError(self._peek(), "Expect expression")

  
  def _is_at_end(self) -> bool:   
    return self._peek().kind == TokenType.EOF

  def _match(self, kind : TokenType) -> bool:
    
    return not self._is_at_end() and self._peek().kind == kind

  def _consume(self, *args : tuple) -> bool:
    
    for token in args:
      if self._match(token):
        self._advance(); return True       
    
    return False

  def _peek(self) -> Token:
    return self._tokens[self._current]

  def _previous(self) -> Token:
    return self._tokens[self._current - 1]

  def _advance(self) -> Token:
    if not self._is_at_end():
      self._current += 1
    return self._previous()

  def _expect(self, expected : TokenType, err_msg : str) -> Token:
    if self._match(expected):
      return self._advance()
    else:
      raise ParseError(self._peek(), err_msg)
    

