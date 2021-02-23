
from .token import *
from .token_type import *
from .expr import *
from .stmt import *
from .errors import ParseError, error_collector

class Obj : # for Variable description
  def __init__(self, offset : int = 0) :
    self.offset = offset

class Parser :
  
  _tokens = []
  _current = 0
  
  _lvars = {}
  _offset = 0 

  @classmethod
  def parse(cls, tokens : list) -> Function :

    cls._tokens = tokens    

    statements = [] # function's body

    while not cls._is_at_end() :
      try:
        stmt = cls._statement()

      except ParseError as err :
        error_collector.add(err)
        cls._syncronize(); continue
      else:
        # it only appends if no errors occurred during parsing
        # it's a valid statement
        statements.append(stmt) 

    return Function(cls._lvars, body = statements, stack_size = cls._offset)

  @classmethod
  def _statement(cls) -> Stmt:
    # statement -> exprStmt
    return cls._exprStmt()

  @classmethod
  def _exprStmt(cls) -> Stmt:
    """
       matches the rule :
         exprStmt -> expression ";"
    """
    expr = cls._expression()
    cls._expect(TokenType.SEMICOLON, err_msg = "expected ';' after expression")
    
    return Expression(expr) 

  @classmethod
  def _expression(cls) -> Expr:
    
    """
       matches the rule: 
         expression -> assignment
    """
    return cls._assignment()

  @classmethod
  def _assignment(cls) -> Expr:
    
    """ 
       matches the rule: 
         assignment -> equality ("=" assignment)?
    """
    expr = cls._equality()

    if cls._consume(TokenType.EQUAL) :
      equals = cls._previous()
      
      if not isinstance(expr, Variable) :
        raise ParseError(equals, "not an lvalue")

      value = cls._assignment()
      expr = Assign(expr, value)

    return expr

  @classmethod
  def _equality(cls) -> Expr:
    
    """
       matches to one of the rules: 
         equality -> comparison ("==" comparison)*
         equality -> comparison ("!=" comparison)*
    """

    left = cls._comparison()

    while cls._consume(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL) :
      operator = cls._previous()
      right = cls._comparison()

      left = Relational(left, operator, right)

    return left
  
  @classmethod
  def _comparison(cls) -> Expr:

    """
       matches to one of the rules: 
         comparison -> addition ( "<" addition)*
         comparison -> addition ("<=" addition)*
         comparison -> addition ( ">" addition)*
         comparison -> addition (">=" addition)*
    """    

    left = cls._addition()

    while cls._consume(TokenType.LESS, TokenType.LESS_EQUAL, 
                        TokenType.GREATER, TokenType.GREATER_EQUAL) :
      
      operator = cls._previous()

      right = cls._addition()

      if operator.kind in {TokenType.GREATER, TokenType.GREATER_EQUAL} :
        # don't need to support > and >= Assembly instructions, so A >= B will be translated to B <= A
        left = Relational(right, operator, left)  
      else:
        left = Relational(left, operator, right)

    return left

  @classmethod
  def _addition(cls) -> Expr:
    
    """
       matches to one of the rules: 
         addition -> multiplication ("+" multiplication)*
         addition -> multiplication ("-" multiplication)*
    """    

    left = cls._multiplication()
    
    while cls._consume(TokenType.PLUS, TokenType.MINUS) :
      operator = cls._previous()
      right = cls._multiplication()
     
      left = Binary(left, operator, right)

    return left

  @classmethod
  def _multiplication(cls) -> Expr:
    
    """
       matches to one of the rules: 
         multiplication -> unary ("*" unary)*
         multiplication -> unary ("/" unary)*
    """

    left = cls._unary()
        
    while cls._consume(TokenType.SLASH, TokenType.STAR) :
      operator = cls._previous()
      right = cls._unary()
     
      left = Binary(left, operator, right)

    return left

  @classmethod
  def _unary(cls) -> Expr :
    
    """
       matches to one of the rules:
         unary -> ("+" | "-")? unary
         unary -> primary    
    """

    if cls._consume(TokenType.PLUS) :
      return cls._unary()

    if cls._consume(TokenType.MINUS) :
      operator = cls._previous()
      left = cls._unary()      

      return Unary(left, operator)

    return cls._primary()

  @classmethod
  def _primary(cls) -> Expr:
    
    """
       matches to one of the rules:
         primary -> NUMBER
         primary -> IDENTIFIER
         primary -> "(" expression ")"
    """

    if cls._consume(TokenType.NUM) :
      return Literal(cls._previous().literal)

    elif cls._consume(TokenType.IDENTIFIER) :
      
      var_name = cls._previous().lexeme

      if not var_name in cls._lvars :
        cls._offset += 8
        cls._lvars[var_name] = Obj(-cls._offset)

      return Variable(var_name, var_desc = cls._lvars[var_name])

    elif cls._consume(TokenType.LEFT_PAREN) :
      
      left = cls._expression()
      cls._expect(TokenType.RIGHT_PAREN, err_msg = "expected ')' after expression")
      
      return left

    else :
      raise ParseError(cls._peek(), "invalid expression")

  @classmethod 
  def _is_at_end(cls) -> bool:   
    return cls._peek().kind == TokenType.EOF

  @classmethod
  def _match(cls, kind : TokenType) -> bool:

    return not cls._is_at_end() and cls._peek().kind == kind

  @classmethod
  def _consume(cls, *args : tuple) -> bool:
    
    for token in args :
      if cls._match(token) :
        cls._current += 1 
        return True      
    
    return False

  @classmethod
  def _peek(cls) -> Token:
    return cls._tokens[cls._current]

  @classmethod
  def _previous(cls) -> Token:
    return cls._tokens[cls._current - 1]

  @classmethod
  def _advance(cls) -> Token:
    if not cls._is_at_end():
      cls._current += 1
    return cls._previous()

  @classmethod
  def _expect(cls, expected : TokenType, err_msg : str) -> Token:
    if cls._match(expected):
      return cls._advance()
    else:
      raise ParseError(cls._peek(), err_msg)
    
  @classmethod
  def _syncronize(cls) -> None :
  
    begin_statement = {}
    end_statement = {TokenType.SEMICOLON}

    while not cls._is_at_end() :

      if cls._previous().kind in end_statement : return
      elif cls._peek().kind in begin_statement : return
      else : cls._current += 1


