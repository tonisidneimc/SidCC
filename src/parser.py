
from .token import *
from .token_type import *
from .expr import *
from .stmt import *
from .errors import ParseError, error_collector

class Parser :
  
  def __init__(self, tokens : list) :
    self._current = 0
    self._tokens = tokens    

  def parse(self) -> list :
    statements = []
    
    while not self._is_at_end() :
      try:
        stmt = self._statement()

      except ParseError as err :
        error_collector.add(err)
        self._syncronize(); continue
      else:
        statements.append(stmt)

    return statements

  def _statement(self) -> Stmt:

    return self._exprStmt()

  def _exprStmt(self) -> Stmt:

    expr = self._expression()
    self._expect(TokenType.SEMICOLON, err_msg = "expected ';' after expression")
    
    return Expression(expr) 

  def _expression(self) -> Expr:
    
    return self._assignment()

  def _assignment(self) -> Expr:
    
    expr = self._equality()

    if self._consume(TokenType.EQUAL) :
      equals = self._previous()
      
      if not isinstance(expr, Variable) :
        raise ParseError(equals, "not an lvalue")

      value = self._assignment()
      expr = Assign(expr, value)

    return expr

  def _equality(self) -> Expr:

    left = self._comparison()

    while self._consume(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL) :
      operator = self._previous()
      right = self._comparison()

      left = Relational(left, operator, right)

    return left
  
  def _comparison(self) -> Expr:

    left = self._addition()

    while self._consume(TokenType.LESS, TokenType.LESS_EQUAL, 
                        TokenType.GREATER, TokenType.GREATER_EQUAL) :
      
      operator = self._previous()

      right = self._addition()

      if operator.kind in {TokenType.GREATER, TokenType.GREATER_EQUAL} :
        # don't need to support > and >= Assembly instructions, so A >= B will be translated to B <= A
        left = Relational(right, operator, left)  
      else:
        left = Relational(left, operator, right)

    return left

  def _addition(self) -> Expr:
    
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

    elif self._consume(TokenType.IDENTIFIER) :
      return Variable(self._previous().lexeme)

    elif self._consume(TokenType.LEFT_PAREN) :
      left = self._expression()
      self._expect(TokenType.RIGHT_PAREN, err_msg = "expected ')' after expression")
      
      return left

    else :
      raise ParseError(self._peek(), "invalid expression")

  
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
    
  def _syncronize(self) -> None :
  
    begin_statement = {}
    end_statement = {TokenType.SEMICOLON}

    while not self._is_at_end() :

      if self._previous().kind in end_statement :
        return
      elif self._peek().kind in begin_statement :
        return
      else : 
        self._advance()



