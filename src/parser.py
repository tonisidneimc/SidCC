
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
  def parse(cls, tokens : list) -> list:

    cls._tokens = tokens
    cls._current = 0

    cls._prog = [] # prog -> function*

    # map fname -> index of function in prog
    cls._env = dict()

    while not cls._is_at_end() :
      try:
        fn = cls._function()
      except SyntaxErr as err:
        error_collector.add(err)
        cls._syncronize(); continue
      else:
        cls._env[fn.name] = len(cls._prog)
        cls._prog.append(fn)

    return cls._prog

  @classmethod
  def _declspec(cls) -> DataType:

    cls._expect(TokenType.INT, err_msg = "expected specifier or declaration")
    return ty_int

  @classmethod
  def _declarator(cls, basetype : DataType) -> tuple:

    data_type = basetype

    while cls._match(TokenType.STAR) :
      data_type = Pointer_to(data_type)
      cls._consume_current()

    try:
      var_name = cls._expect(TokenType.IDENTIFIER, err_msg = "expected a identifier")

      if cls._match(TokenType.LEFT_SQUARE_BRACE) :
        cls._consume_current() # consumes '['
        size = cls._expect(TokenType.NUM, err_msg = "expected a number").literal
        cls._expect(TokenType.RIGHT_SQUARE_BRACE, err_msg = "expected ']'")
        data_type = Array_of(data_type, size)

    except SyntaxErr : raise 

    else : return data_type, var_name.lexeme

  @classmethod
  def _new_lvar(cls, var_name : str, data_type : DataType) :
    
    cls._offset += data_type.size
    var_desc = Object(data_type, -(cls._offset))
    cls._lvars[var_name] = var_desc
    return var_desc

  @classmethod
  def _func_params(cls) -> list:
    """
       func_params -> param ("," param)*
    """
    params = []
      
    while not cls._is_at_end() :
      try:
        if cls._match(TokenType.RIGHT_PAREN) : break

        basetype = cls._declspec()
        data_type, var_name = cls._declarator(basetype)

        param = cls._new_lvar(var_name, data_type)

      except SyntaxErr as err: raise
      else :
        params.append(param)

        if not cls._match(TokenType.COMMA) : break
        cls._consume_current()

    return params 

  @classmethod
  def _function(cls) -> FunctionStmt:
    
    cls._lvars = dict() # map of local variables
    cls._offset = 0     # offset of each local variable

    try:
      e_brace = 1
      basetype = cls._declspec()
      ret_type, fname = cls._declarator(basetype)
      ret_type = Function(ret_type)

      cls._expect(TokenType.LEFT_PAREN, err_msg = "expected '('")
      
      params = cls._func_params() # func_params -> param ("," param)
      
      cls._expect(TokenType.RIGHT_PAREN, err_msg = "expected ')'")
      cls._expect(TokenType.LEFT_CURLY_BRACE, err_msg = "expected '{'")

      body = cls._compoundStmt()
      e_brace = 0

    except SyntaxErr as err:
      # panicked at function definition, exit from function's block
      cls._consume_current()
 
      while not cls._is_at_end() :
        if cls._match(TokenType.RIGHT_CURLY_BRACE) :
          if e_brace == 1 :
            cls._current += 1; break;
          e_brace -= 1
          
        elif cls._match(TokenType.LEFT_CURLY_BRACE) : e_brace += 1

        cls._current += 1
      raise
    else: 
      return FunctionStmt(fname, params, cls._lvars, body, ret_type, stack_size=cls._offset)

  @classmethod
  def _declaration(cls) -> Stmt:

    basetype = cls._declspec()

    declarations = []

    while not cls._is_at_end():

      if cls._match(TokenType.SEMICOLON) : break

      data_type, var_name = cls._declarator(basetype)

      if var_name in cls._lvars:
        raise SyntaxErr(cls._previous(), "'%s' redeclared" %(var_name))
      else:
        var_desc = cls._new_lvar(var_name, data_type)
        
      if cls._match(TokenType.EQUAL) :
        equals = cls._consume_current()
        # var = assignment
        left  = VariableExpr(var_name, var_desc)
        right = cls._assignment()
        decl = ExpressionStmt(AssignExpr(left, equals, right))
        declarations.append(decl)

      if not cls._match(TokenType.COMMA) : break
      cls._consume_current() # consumes ',' and continue

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
    statements = {
      TokenType.IF               : cls._ifStmt,
      TokenType.FOR              : cls._forStmt,
      TokenType.WHILE            : cls._whileStmt,
      TokenType.LEFT_CURLY_BRACE : cls._compoundStmt,
      TokenType.RETURN           : cls._returnStmt,
    }

    token_kind = cls._peek().kind

    if token_kind in statements:
      cls._consume_current()
      return statements[token_kind]()
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

    while not cls._match(TokenType.RIGHT_CURLY_BRACE) :
      
      if cls._is_at_end() : break

      try :
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
    cls._expect(TokenType.RIGHT_CURLY_BRACE, err_msg = "expected '}'")

    return CompoundStmt(statements)

  @classmethod
  def _ifStmt(cls) -> Stmt:
    """
       matches the rule:
         ifStmt -> "if" "(" expression ")" statement ("else" statement)?
    """
    # 'if' was previously consumed
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
    # 'for' was previously consumed
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
    # 'while' was previously consumed
    cls._expect(TokenType.LEFT_PAREN, err_msg = "expected '(' after 'while'")
    condition = cls._expression()
    cls._expect(TokenType.RIGHT_PAREN, err_msg = "expected ')' after condition")

    body = cls._statement()

    # init = None, increment = None
    return ForStmt(None, condition, None, body)

  @classmethod
  def _returnStmt(cls) -> Stmt:    
    """
       matches the rule:
         returnStmt -> "return" expression? ";"
    """
    # 'return' was previously consumed
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
    left = cls._equality()

    if cls._match(TokenType.EQUAL) :

      equals = cls._consume_current()

      try:
        # can only cascade variables and dereferences in an assignment
        assert left.is_variable or (left.is_unary and left.is_deref)
      except AssertionError:
        raise SyntaxErr(equals, "not an lvalue")
      else:  
        right = cls._assignment()
        left = AssignExpr(left, equals, right)
        left.operand_type = cls._add_type(left)

    return left

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
      left.operand_type = cls._add_type(left)

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

      left.operand_type = cls._add_type(left)

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
      except SyntaxErr as err: raise

      # num + num
      if left.operand_type.is_integer and right.operand_type.is_integer:
        left = BinaryExpr(left, operator, right)
        left.operand_type = cls._add_type(left)

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
            mul_op = copy(operator); mul_op.kind = TokenType.STAR
            right = BinaryExpr(right, mul_op, LiteralExpr(left.operand_type.base.size))
            left = BinaryExpr(left, operator, right)
            left.operand_type = cls._add_type(left)
      
        else: # operator.kind == TokenType.MINUS
          
          # ptr - num
          if left.operand_type.is_pointer and right.operand_type.is_integer:
            mul_op = copy(operator); mul_op.kind = TokenType.STAR
            right = BinaryExpr(right, mul_op, LiteralExpr(left.operand_type.base.size))
            left = BinaryExpr(left, operator, right)
            left.operand_type = cls._add_type(left)

          # ptr - ptr, how many elements are between the two  
          elif left.operand_type.is_pointer and right.operand_type.is_pointer:
            left = BinaryExpr(left, operator, right)
            left.operand_type = ty_int
            div_op = copy(operator); div_op.kind = TokenType.SLASH
            left = BinaryExpr(left, div_op, LiteralExpr(left.operand_type.size))

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
      left.operand_type = cls._add_type(left)

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
      left = UnaryExpr(left, operator)
      left.operand_type = cls._add_type(left)
      return left

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
      try: # parse args
        arg = cls._assignment()

      except SyntaxErr: raise
      else:
        arg.operand_type = cls._add_type(arg)
        arg_list.append(arg) # if no errors

      if not cls._match(TokenType.COMMA) : break 
        
      cls._consume_current() # consumes ',' 

    cls._expect(TokenType.RIGHT_PAREN, err_msg = "expected ')'")

    fname = obj_name.lexeme
    try:
      if not fname in cls._env :
        # warning: function undeclared
        raise SyntaxErr(obj_name, "implicit declaration of function '%s'" %(fname), True)

    except SyntaxErr as err:
      error_collector.add(err) # non-critical
      return FunCallExpr(fname, arg_list)

    fn = cls._prog[cls._env[fname]]
  
    i = 0; # iterate over the arguments list and check for type mismatches
    while i < min(len(arg_list), fn.arity) :
      try: # report all type mismatches
        if arg_list[i].operand_type != fn.params[i].data_type :
          raise SyntaxErr(obj_name, "expected '%s' but argument %d is of type '%s'"
                        %(str(fn.params[i].data_type), i+1, str(arg_list[i].operand_type)))
      except SyntaxErr as err :
        error_collector.add(err) # non-critical ?

      finally: i += 1

    try:
      if len(arg_list) < fn.arity :  # critical
        raise SyntaxErr(obj_name, "too few arguments to function '%s'" %(fname))
      elif len(arg_list) > fn.arity :  # critical
        raise SyntaxErr(obj_name, "too many arguments to function '%s'" %(fname))

    except SyntaxErr : raise

    else : return FunCallExpr(fname, arg_list)

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

      obj_name = cls._consume_current()

      # function call -> IDENTIFIER "(" args ")"
      if cls._match(TokenType.LEFT_PAREN) :
        return cls._funcall(obj_name)

      # variable -> IDENTIFIER
      else :
        var_name = obj_name.lexeme
        if not var_name in cls._lvars:
          raise SyntaxErr(cls._previous(), "'%s' undeclared" %(var_name))
        
        var_desc = cls._lvars[var_name]
        left = VariableExpr(var_name, var_desc)
        left.operand_type = var_desc.data_type
        return left

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
    if cls._current >= len(cls._tokens) : return True
    else : return cls._peek().kind == TokenType.EOF

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
    if cls._is_at_end() :
      raise SyntaxErr(cls._previous(), err_msg + " at end of input")
    elif cls._peek().kind == expected:
      cls._current += 1
      return cls._previous()
    else:
      raise SyntaxErr(cls._peek(), err_msg)
    
  @classmethod
  def _syncronize(cls) -> None :

    begin_statement = {
      TokenType.LEFT_CURLY_BRACE,
      TokenType.IF,
      TokenType.FOR, TokenType.WHILE,
      TokenType.INT,
      TokenType.RETURN,
    }
    end_statement = {TokenType.SEMICOLON, TokenType.RIGHT_CURLY_BRACE}

    while not cls._is_at_end() :
      if cls._previous().kind in end_statement : return
      elif cls._peek().kind in begin_statement : return
      else : cls._current += 1

  @classmethod
  def _add_type(cls, node : Expr) -> DataType:

    if node.operand_type is not None:
      return node.operand_type

    elif node.is_variable:
      return node.operand_type

    elif node.is_literal or (node.is_binary and node.is_relational) or node.is_funcall:
      return ty_int

    elif (node.is_unary and node.is_neg) or (node.is_binary and node.is_arithmetic):
      return cls._add_type(node.lhs)

    elif node.is_assignment:
      operand_type = cls._add_type(node.lhs)
      if operand_type.is_array :
        raise SyntaxErr(node.equals, "not an lvalue")
      return operand_type

    elif (node.is_unary and node.is_addressing):
      operand_type = cls._add_type(node.lhs)
      if operand_type.is_array :
        # array of something -> pointer to something
        return Pointer_to(operand_type.base)
      else:
        return Pointer_to(operand_type)

    elif node.is_deref:
      operand_type = cls._add_type(node.lhs)

      if not operand_type.is_pointer:
        raise SyntaxErr(node.op, "invalid pointer dereference")

      return operand_type.base
      

