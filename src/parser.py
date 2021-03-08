
from .token import *
from .token_type import *
from .expr import *
from .stmt import *
from .errors import SyntaxErr, error_collector

class Object : # for Variable description
  def __init__(self, offset : int = 0) :
    self.offset = offset

class Parser : 

  @classmethod
  def parse(cls, tokens : list) -> FunctionStmt :

    cls._tokens = tokens
    cls._current = 0

    cls._lvars = dict()
    cls._offset = 0

    try:
      if cls._match(TokenType.LEFT_BRACE) :
        cls._consume_current()
        body = cls._compoundStmt()
      else :
        body = None
    except SyntaxErr as err :
      error_collector.add(err)
      return None # ensure later that it won't be compiled
    else:
      return FunctionStmt(cls._lvars, body, stack_size = cls._offset)   

  @classmethod
  def _statement(cls) -> Stmt:
    """
       matches to one of the rules :
         statement -> exprStmt
         statement -> ifStmt
         statement -> compoundStmt
         statement -> forStmt
         statement -> returnStmt
    """
    _statements = {
      TokenType.IF         : cls._ifStmt,
      TokenType.FOR        : cls._forStmt,
      TokenType.WHILE      : cls._whileStmt,
      TokenType.RETURN     : cls._returnStmt,
      TokenType.LEFT_BRACE : cls._compoundStmt,
    }

    token_kind = cls._peek().kind

    if token_kind in _statements:
      cls._consume_current()
      return _statements[token_kind]()
    else :
      return cls._exprStmt()
  
  @classmethod
  def _compoundStmt(cls) -> Stmt:
    """
       matches the rule:
         compoundStmt -> "{" statement* "}"
    """
    statements = []
    
    while not cls._match(TokenType.RIGHT_BRACE) :
      
      if cls._is_at_end() : break

      try:
        stmt = cls._statement()
      except SyntaxErr as err:
        error_collector.add(err)
        cls._syncronize(); continue
      else:
        # it only appends if no errors occurred during parsing
        # it's a valid statement
        statements.append(stmt)
    
    # it will consume correspondents '}' until EOF
    cls._expect(TokenType.RIGHT_BRACE, err_msg = "expected declaration or statement at end of input")

    return CompoundStmt(statements)

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

    else_branch = None
    if cls._match(TokenType.ELSE) :
      cls._consume_current()
      else_branch = cls._statement()
    
    return IfStmt(condition, then_branch, else_branch) 

  @classmethod 
  def _forStmt(cls) -> Stmt:
    """
       matches the rule:  
         forStmt -> "for" "(" exprStmt expression? ";" expression? ")" statement
    """
    cls._expect(TokenType.LEFT_PAREN, err_msg = "expected '(' after 'for'")
    initializer = cls._exprStmt()

    condition = cls._expression() if not cls._match(TokenType.SEMICOLON) else None
    cls._consume_current() # consumes ';'

    increment = cls._expression() if not cls._match(TokenType.RIGHT_PAREN) else None
    cls._expect(TokenType.RIGHT_PAREN, err_msg = "expected ')'")

    body = cls._statement()
 
    return ForStmt(initializer, condition, increment, body)  

  @classmethod
  def _whileStmt(cls) -> Stmt:
    """
       matches the rule:
         whileStmt -> "while" "(" expression ")" statement
    """
    cls._expect(TokenType.LEFT_PAREN, err_msg = "expected '(' after 'while'")
    condition = cls._expression()
    cls._expect(TokenType.RIGHT_PAREN, err_msg = "expected ')' after condition")

    body = cls._statement()

    return ForStmt(init = None, cond = condition, inc = None, body = body)

  @classmethod
  def _returnStmt(cls) -> Stmt:    
    """
       matches the rule:
         returnStmt -> "return" expression? ";"
    """
    value = cls._expression() if not cls._match(TokenType.SEMICOLON) else None

    cls._expect(TokenType.SEMICOLON, err_msg = "expected ';' after expression")
  
    return ReturnStmt(value)

  @classmethod
  def _exprStmt(cls) -> Stmt:
    """
       matches the rule :
         exprStmt -> expression? ";"
    """
    expr = cls._expression() if not cls._match(TokenType.SEMICOLON) else None

    cls._expect(TokenType.SEMICOLON, err_msg = "expected ';' after expression")
    
    return ExpressionStmt(expr) 

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

    if cls._match(TokenType.EQUAL) :

      equals = cls._consume_current()

      try:
        # can only cascade variables and dereferences in an assignment
        assert expr.is_variable or (expr.is_unary and expr.is_deref)
      except AssertionError:
        raise SyntaxErr(equals, "not an lvalue")
      else:  
        value = cls._assignment()
        expr = AssignExpr(expr, value)

    return expr

  @classmethod
  def _equality(cls) -> Expr:
    
    """
       matches to one of the rules: 
         equality -> comparison ("==" comparison)*
         equality -> comparison ("!=" comparison)*
    """

    left = cls._comparison()

    while cls._match(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL) :
      operator = cls._consume_current()
      right = cls._comparison()

      left = BinaryExpr(left, operator, right)

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

    while cls._match(TokenType.LESS, TokenType.LESS_EQUAL, 
                     TokenType.GREATER, TokenType.GREATER_EQUAL) :
      
      operator = cls._consume_current()

      right = cls._addition()

      if operator.kind in {TokenType.GREATER, TokenType.GREATER_EQUAL} :
        # don't need to support > and >= Assembly instructions, so A >= B will be translated to B <= A
        left = BinaryExpr(right, operator, left)  
      else:
        left = BinaryExpr(left, operator, right)

    return left

  @classmethod
  def _addition(cls) -> Expr:
    
    """
       matches to one of the rules: 
         addition -> multiplication ("+" multiplication)*
         addition -> multiplication ("-" multiplication)*
    """    

    left = cls._multiplication()
    
    while cls._match(TokenType.PLUS, TokenType.MINUS) :
      operator = cls._consume_current()
      right = cls._multiplication()
     
      left = BinaryExpr(left, operator, right)

    return left

  @classmethod
  def _multiplication(cls) -> Expr:
    
    """
       matches to one of the rules: 
         multiplication -> unary ("*" unary)*
         multiplication -> unary ("/" unary)*
    """

    left = cls._unary()
        
    while cls._match(TokenType.SLASH, TokenType.STAR) :
      operator = cls._consume_current()
      right = cls._unary()
     
      left = BinaryExpr(left, operator, right)

    return left

  @classmethod
  def _unary(cls) -> Expr :
    
    """
       matches to one of the rules:
         unary -> ("+" | "-" | "&" | "*")? unary
         unary -> primary    
    """

    if cls._match(TokenType.PLUS) : # ignores it
      cls._consume_current()
      return cls._unary()

    elif cls._match(TokenType.MINUS, TokenType.AMPERSAND, TokenType.STAR) :
      operator = cls._consume_current()
      left = cls._unary()      

      return UnaryExpr(left, operator)

    return cls._primary()

  @classmethod
  def _primary(cls) -> Expr:
    
    """
       matches to one of the rules:
         primary -> NUMBER
         primary -> IDENTIFIER
         primary -> "(" expression ")"
    """

    if cls._match(TokenType.NUM) :
      curr_token = cls._consume_current()
      return LiteralExpr(curr_token.literal)

    elif cls._match(TokenType.IDENTIFIER) :
      
      var_name = cls._consume_current().lexeme

      if not var_name in cls._lvars :
        cls._offset += 8
        cls._lvars[var_name] = Object(-(cls._offset))

      return VariableExpr(var_name, var_desc = cls._lvars[var_name])

    elif cls._match(TokenType.LEFT_PAREN) :
      # grouping expression
      cls._consume_current()
      left = cls._expression()
      cls._expect(TokenType.RIGHT_PAREN, err_msg = "expected ')' after expression")
      
      return left

    else :
      raise SyntaxErr(cls._peek(), "invalid expression")

  @classmethod
  def _peek(cls) -> Token:
    return cls._tokens[cls._current]

  @classmethod
  def _previous(self) -> Token :
    #returns the last consumed Token from _tokens
    return self._tokens[self._current - 1]

  @classmethod 
  def _is_at_end(cls) -> bool:   
    return cls._peek().kind == TokenType.EOF

  @classmethod
  def _match(cls, *args : tuple) -> bool:
    if cls._is_at_end() : 
      return False
    else : 
      for token_kind in args :
        if cls._peek().kind == token_kind:
          return True
      return False

  @classmethod
  def _consume_current(cls) -> Token:
    cls._current += 1
    return cls._previous()

  @classmethod
  def _expect(cls, expected : TokenType, err_msg : str) -> Token:
    if cls._match(expected):
      cls._current += 1
      return cls._previous()
    else:
      raise SyntaxErr(cls._peek(), err_msg)
    
  @classmethod
  def _syncronize(cls) -> None :
  
    begin_statement = {
      TokenType.IF,
      TokenType.FOR, TokenType.WHILE,
      TokenType.RETURN,
    }
    end_statement = {TokenType.SEMICOLON, TokenType.RIGHT_BRACE}

    while not cls._is_at_end() :

      if cls._previous().kind in end_statement : return
      elif cls._peek().kind in begin_statement : return
      else : cls._current += 1


