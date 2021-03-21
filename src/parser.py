
from copy import copy

from .token import *
from .token_type import *
from .data_type import *
from .expr import *
from .stmt import *
from .errors import SyntaxErr, error_collector

class Object : # for Variable description
  def __init__(self, data_type : DataType, offset : int = 0) :
    self.data_type = data_type 
    self.offset = offset

class Parser : 

  @classmethod
  def parse(cls, tokens : list) -> FunctionStmt :

    cls._tokens = tokens
    cls._current = 0

    cls._lvars = dict()
    cls._offset = 0

    try:
      cls._expect(TokenType.LEFT_BRACE, err_msg = "expected '{'")
      body = cls._compoundStmt()
    except SyntaxErr as err :
      error_collector.add(err)
      return None # ensure later that it won't be compiled
    else:
      return FunctionStmt(cls._lvars, body, stack_size = cls._offset)   

  @classmethod
  def _declspec(cls) -> DataType:
    
    cls._expect(TokenType.INT, err_msg = "expected specifier or declaration")
    return ty_int

  @classmethod
  def _declarator(cls, basetype : DataType) -> DataType:

    data_type = basetype    

    while cls._match(TokenType.STAR) :
      data_type = Pointer_to(data_type)
      cls._consume_current()

    if not cls._match(TokenType.IDENTIFIER):
      raise SyntaxErr(cls._peek(), "expected a variable name")

    return data_type

  @classmethod
  def _declaration(cls) -> Stmt:

    basetype = cls._declspec()

    declarations = []

    while not cls._is_at_end():

      if cls._match(TokenType.SEMICOLON) : break

      data_type = cls._declarator(basetype)

      var_name = cls._consume_current().lexeme

      if var_name in cls._lvars:
        raise SyntaxErr(cls._previous(), "'%s' redeclared" %(var_name))

      # else
      cls._offset += 8
      var_desc = Object(data_type, -(cls._offset))
      cls._lvars[var_name] = var_desc

      if cls._match(TokenType.EQUAL) :
        cls._consume_current() 

        # var = assignment
        left  = VariableExpr(var_name, var_desc)
        right = cls._assignment()
        decl = ExpressionStmt(AssignExpr(left, right))
        declarations.append(decl)

      if not cls._match(TokenType.COMMA) : break
      
      cls._consume_current()

    cls._expect(TokenType.SEMICOLON, "expected ';'")

    return CompoundStmt(declarations)

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
         compoundStmt -> "{" (declaration | statement)* "}"
    """
    statements = []

    # '{' was previously consumed    

    while not cls._match(TokenType.RIGHT_BRACE) :
      
      if cls._is_at_end() : break

      try:
        if cls._match(TokenType.INT) :
          stmt = cls._declaration()
        else : 
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

      try:
        left.operand_type  = cls._add_type(left)
        right.operand_type = cls._add_type(right)
      except SyntaxErr as err:
        raise

      # num + num
      if left.operand_type.is_integer and right.operand_type.is_integer:
        left = BinaryExpr(left, operator, right)

      else:
        # parse pointer arithmetic      

        if operator.kind == TokenType.PLUS:
  
          # ptr + ptr
          if left.operand_type.is_pointer and right.operand_type.is_pointer:
            raise SyntaxErr(operator, "invalid operands")

          else:
            if left.operand_type.is_integer and right.operand_type.is_pointer:
              # convert 'num + ptr' to 'ptr + num'
              left, right = right, left

            # convert 'ptr + num' to 'ptr + (num * 8)'
            _operator = copy(operator); _operator.kind = TokenType.STAR
            right = BinaryExpr(right, _operator, LiteralExpr(8))
            left = BinaryExpr(left, operator, right)
      
        else: # operator.kind == TokenType.MINUS
          
          # ptr - num
          if left.operand_type.is_pointer and right.operand_type.is_integer:
            _operator = copy(operator); _operator.kind = TokenType.STAR
            right = BinaryExpr(right, _operator, LiteralExpr(8))
            left = BinaryExpr(left, operator, right)

          # ptr - ptr, how many elements are between the two  
          elif left.operand_type.is_pointer and right.operand_type.is_pointer:
            left = BinaryExpr(left, operator, right)
            _operator = copy(operator); _operator.kind = TokenType.SLASH
            left = BinaryExpr(left, _operator, LiteralExpr(8))
            left.operand_type = ty_int

          else:
            raise SyntaxErr(operator, "invalid operands")
        
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
  def _funcall(cls, obj_name : str) -> Expr:
    """
       matches the rule:
         funcall -> IDENTIFIER "(" ( assignment ("," assignment)*)? ")"
    """
    cls._consume_current() # consumes '('

    arg_list = []

    while not cls._match(TokenType.RIGHT_PAREN) :
      try:
        arg = cls._assignment()
      except SyntaxErr:
        raise
      else:
        arg_list.append(arg)

      if not cls._match(TokenType.COMMA) : break 
        
      cls._consume_current() # consumes ','
         
    cls._expect(TokenType.RIGHT_PAREN, err_msg = "expected ')'")
    
    return FunCallExpr(obj_name, arg_list) 

  @classmethod
  def _primary(cls) -> Expr:
    
    """
       matches to one of the rules:
         primary -> NUMBER
         primary -> IDENTIFIER
         primary -> funcall
         primary -> "(" expression ")"
    """

    if cls._match(TokenType.NUM) :
      curr_token = cls._consume_current()
      return LiteralExpr(curr_token.literal)

    elif cls._match(TokenType.IDENTIFIER) :
      
      obj_name = cls._consume_current().lexeme

      # function call
      if cls._match(TokenType.LEFT_PAREN) :
        return cls._funcall(obj_name)

      # variable
      else :
        if not obj_name in cls._lvars:
          raise SyntaxErr(cls._previous(), "'%s' undeclared" %(obj_name))
        
        return VariableExpr(obj_name, var_desc = cls._lvars[obj_name])

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

  @classmethod
  def _add_type(cls, node : Expr) -> DataType:

    if node.operand_type is not None:
      return node.operand_type

    elif node.is_literal or node.is_variable or (node.is_binary and node.is_relational) or node.is_funcall:
      return ty_int

    elif (node.is_unary and node.is_neg) or (node.is_binary and node.is_arithmetic) or node.is_assignment:
      return cls._add_type(node.lhs)

    elif (node.is_unary and node.is_addressing):
      base = cls._add_type(node.lhs)
      return Pointer_to(base)

    elif node.is_deref:
      operand_type = cls._add_type(node.lhs)

      if not operand_type.is_pointer:
        raise SyntaxErr(node.operator, err_msg = "invalid pointer dereference")

      return operand_type.base
      

