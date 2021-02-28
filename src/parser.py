
from .token import *
from .token_type import *
from .expr import *
from .stmt import *
from .errors import ParseError, error_collector

class Obj : # for Variable description
  def __init__(self, offset : int = 0) :
    self.offset = offset

class Parser : 

  @classmethod
  def parse(cls, tokens : list) -> Function :

    cls._tokens = tokens
    cls._current = 0

    cls._lvars = dict()
    cls._offset = 0

    try:
      body = cls._block() if cls._consume(TokenType.LEFT_BRACE) else None
    except ParseError as err :
      error_collector.add(err)
      return None
    else:
      return Function(cls._lvars, body, stack_size = cls._offset)   

  @classmethod
  def _statement(cls) -> Stmt:
    """
       matches to one of the rules :
         statement -> exprStmt
         statement -> ifStmt
         statement -> forStmt
         statement -> returnStmt
         statement -> block
    """
    if cls._consume(TokenType.IF) :
      return cls._ifStmt()
    elif cls._consume(TokenType.FOR) :
      return cls._forStmt()
    elif cls._consume(TokenType.RETURN):
      return cls._returnStmt()
    elif cls._consume(TokenType.LEFT_BRACE):
      return cls._block()
    else :
      return cls._exprStmt()
  
  @classmethod
  def _block(cls) -> Stmt:
    """
       matches the rule:
         block -> "{" statement* "}"
    """
    
    statements = []
    
    while not(cls._is_at_end() or cls._match(TokenType.RIGHT_BRACE)) :
      try:
        stmt = cls._statement()
      except ParseError as err:
        error_collector.add(err)
        cls._syncronize(); continue
      else:
        # it only appends if no errors occurred during parsing
        # it's a valid statement
        statements.append(stmt)
    
    # it will consume correspondents '}' until EOF
    cls._expect(TokenType.RIGHT_BRACE, err_msg = "expected declaration or statement at end of input")

    return Block(statements)

  @classmethod
  def _ifStmt(cls) -> Stmt:
    """
       matches the rule:
         ifStmt -> "if" "(" expression ")" statement ("else" statement)?
    """
    cls._expect(TokenType.LEFT_PAREN, err_msg = "expected '(' after 'if'")
    condition = cls._expression()
    cls._expect(TokenType.RIGHT_PAREN, err_msg = "expected ')' after if condition")
        
    then_branch = cls._statement()
    else_branch = cls._statement() if cls._consume(TokenType.ELSE) else None 
        
    return If(condition, then_branch, else_branch) 

  @classmethod 
  def _forStmt(cls) -> Stmt:
    """
       matches the rule:  
         forStmt -> "for" "(" exprStmt expression? ";" expression? ")" statement
    """
    cls._expect(TokenType.LEFT_PAREN, err_msg = "expected '(' after 'for'")
    initializer = cls._exprStmt()

    condition = cls._expression() if not cls._match(TokenType.SEMICOLON) else None
    cls._consume(TokenType.SEMICOLON)

    increment = cls._expression() if not cls._match(TokenType.RIGHT_PAREN) else None
    cls._expect(TokenType.RIGHT_PAREN, err_msg = "expected ')'")

    body = cls._statement()
 
    return For(initializer, condition, increment, body)  

  @classmethod
  def _returnStmt(cls) -> Stmt:    
    """
       matches the rule:
         returnStmt -> "return" expression? ";"
    """
    value = cls._expression() if not cls._match(TokenType.SEMICOLON) else None

    cls._expect(TokenType.SEMICOLON, err_msg = "expected ';' after expression")
  
    return Return(value)

  @classmethod
  def _exprStmt(cls) -> Stmt:
    """
       matches the rule :
         exprStmt -> expression? ";"
    """
    expr = cls._expression() if not cls._match(TokenType.SEMICOLON) else None
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

    return cls._peek().kind == kind

  @classmethod
  def _consume(cls, *args : tuple) -> bool:

    if cls._is_at_end() : return False    

    for token_kind in args :
      if cls._match(token_kind) :
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
  def _expect(cls, expected : TokenType, err_msg : str) -> Token:
    if cls._match(expected):
      cls._current += 1
      return cls._previous()
    else:
      raise ParseError(cls._peek(), err_msg)
    
  @classmethod
  def _syncronize(cls) -> None :
  
    begin_statement = {TokenType.RETURN}
    end_statement = {TokenType.SEMICOLON, TokenType.RIGHT_BRACE}

    while not cls._is_at_end() :

      if cls._previous().kind in end_statement : return
      elif cls._peek().kind in begin_statement : return
      else : cls._current += 1


