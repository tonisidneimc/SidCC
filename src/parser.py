
from copy import copy

from .token import *
from .token_type import *
from .data_type import *
from .object_type import *
from .expr import *
from .stmt import *
from .errors import SyntaxErr, error_collector

class Parser :
  
  @classmethod
  def parse(cls, tokens : list) -> list:
    """
       <program> -> declaration*
    """
    cls._tokens = tokens
    cls._current = 0

    cls._globals = []

    while not cls._is_at_end():
      try:
        cls._declaration()
      except SyntaxErr as err:
        error_collector.add(err)
        cls._syncronize()

    return cls._globals

  @classmethod
  def _declspec(cls) -> DataType:
    """
       <declspec> -> "int"
    """
    cls._expect(TokenType.INT, err_msg = "expected specifier or declaration")
    return ty_int

  @classmethod
  def _type_suffix(cls, data_type : DataType) -> DataType:
    """
       <type_suffix> -> "[" NUMBER "]" <type_suffix> | ε
    """
    if cls._match(TokenType.LEFT_BRACKET) :
      cls._consume_current() # consumes '['
      size = cls._expect(TokenType.NUM, err_msg = "expected a number").literal
      cls._expect(TokenType.RIGHT_BRACKET, err_msg = "expected ']'")
      # it evaluates from right to left, 
      # declare int x[2][3]; is array_of(array_of(3, int), 2)
      data_type = cls._type_suffix(data_type)
      return Array_of(data_type, size)

    else : return data_type

  @classmethod
  def _declarator(cls, basetype : DataType) -> tuple:
    """
       <declarator> -> "*"* IDENTIFIER
    """
    data_type = basetype

    while cls._match(TokenType.STAR) :
      data_type = Pointer_to(data_type)
      cls._consume_current()

    try:
      var_name = cls._expect(TokenType.IDENTIFIER, err_msg = "expected a identifier")
    
    except SyntaxErr : raise
    else : 
      return data_type, var_name

  @classmethod
  def _new_lvar(cls, var_name : str, data_type : DataType) :
    
    cls._offset += data_type.size
    var_desc = LVar(data_type, -(cls._offset))
    cls._locals[var_name] = var_desc
    return var_desc

  @classmethod
  def _new_gvar(cls, var_name : str, data_type : DataType) :
  
    var_desc = GVar(data_type, var_name)
    cls._globals.append(var_desc)
    return var_desc

  @classmethod
  def _func_params(cls) -> list:
    """
       <func_params> -> <param> ("," <param>)*
    """
    params = []
      
    while not cls._is_at_end() :
      try:
        if cls._match(TokenType.RIGHT_PAREN) : break

        # <param> -> <declspec> <declarator>
        basetype = cls._declspec()
        data_type, var_name = cls._declarator(basetype)
        param = cls._new_lvar(var_name.lexeme, data_type)

      except SyntaxErr as err: raise
      else :
        params.append(param)

        if not cls._match(TokenType.COMMA) : break
        cls._consume_current() # consumes ','

    return params 

  @classmethod
  def _function(cls, basetype : DataType) -> Fn:
    """
       <function-definition> -> <declspec> <declarator> IDENTIFIER "(" <func-params> ")" "{" <block> "}"
    """
    cls._locals = dict() # map of local variables
    cls._offset = 0      # offset of each local variable

    try:
      e_brace = 1
      ret_type, fname = cls._declarator(basetype)
      ret_type = Function_type(ret_type)

      cls._expect(TokenType.LEFT_PAREN, err_msg = "expected '('")
      
      params = cls._func_params()

      cls._expect(TokenType.RIGHT_PAREN, err_msg = "expected ')'")
      cls._expect(TokenType.LEFT_BRACE, err_msg = "expected '{'")

      body = cls._compoundStmt()
      e_brace = 0

    except SyntaxErr as err:
      cls._consume_current()
      # exit from function's block
      cls._syncronize(e_brace); raise
    else:
      fn = Fn(fname.lexeme, ret_type, params, body, cls._locals, stack_size=cls._offset)
      cls._globals.append(fn)
  
  @classmethod
  def _global_variable(cls, basetype : DataType) :
    # parse declaration of global variables     

    while not cls._match(TokenType.SEMICOLON) :
      data_type, var_name = cls._declarator(basetype)     
      data_type = cls._type_suffix(data_type)

      cls._new_gvar(var_name.lexeme, data_type)
      
      if not cls._match(TokenType.COMMA) : break
      cls._consume_current() # consumes ',' and continue

    cls._expect(TokenType.SEMICOLON, "expected ';'")

  @classmethod
  def _declaration(cls) -> Object:
    """
       declaration -> (<function-definition> | <global-variable>)*
    """
    basetype = cls._declspec()

    start = cls._current
    cls._declarator(basetype) # lookahead to check if it is a function/var declaration
    
    if cls._match(TokenType.LEFT_PAREN) :
      cls._current = start
      return cls._function(basetype)
    else :
      cls._current = start
      return cls._global_variable(basetype)

  @classmethod
  def _var_declaration(cls) -> Stmt:
    """
       <var-declaration> -> <declspec> (<declarator>("=" <expression>)?("," <declarator>("="<expression>)?)*)? ";"
    """
    basetype = cls._declspec()

    declarations = []

    while not cls._is_at_end():

      if cls._match(TokenType.SEMICOLON) : break

      data_type, var_name = cls._declarator(basetype)
      data_type = cls._type_suffix(data_type)

      if var_name.lexeme in cls._locals:
        raise SyntaxErr(var_name, "'%s' redeclared" %(var_name.lexeme))
      else:
        var_desc = cls._new_lvar(var_name.lexeme, data_type)
        
      if cls._match(TokenType.EQUAL) :
        equals = cls._consume_current() # consumes '='
        left  = VariableExpr(var_desc)
        right = cls._assignment()
        decl = ExpressionStmt(AssignExpr(left, equals, right))
        declarations.append(decl)

      if not cls._match(TokenType.COMMA) : break
      cls._consume_current() # consumes ',' and continue

    cls._expect(TokenType.SEMICOLON, "expected ';'")

    return Block(declarations)

  @classmethod
  def _statement(cls) -> Stmt:
    """
       statement -> ifStmt | forStmt | whileStmt | block | returnStmt | exprStmt
    """
    if cls._match(TokenType.IF) :
      return cls._ifStmt()
    elif cls._match(TokenType.FOR) :
      return cls._forStmt()
    elif cls._match(TokenType.WHILE) :
      return cls._whileStmt()
    elif cls._match(TokenType.LEFT_BRACE) :
      cls._consume_current()
      return cls._compoundStmt()
    elif cls._match(TokenType.RETURN) :
      return cls._returnStmt()
    else : 
      return cls._exprStmt()
  
  @classmethod
  def _compoundStmt(cls) -> Stmt:
    """
       <block> -> "{" (<var-declaration> | <statement>)* "}"
    """
    statements = []

    # '{' was previously consumed

    while not cls._match(TokenType.RIGHT_BRACE) :
      
      if cls._is_at_end() : break

      try :
        if cls._match(TokenType.INT) :
          stmt = cls._var_declaration()
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
    cls._expect(TokenType.RIGHT_BRACE, err_msg = "expected '}'")

    return Block(statements)

  @classmethod
  def _ifStmt(cls) -> Stmt:
    """
       <ifStmt> -> "if" "(" <expression> ")" <statement> ("else" <statement>)?
    """
    cls._consume_current()
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
       <forStmt> -> "for" "(" <exprStmt> <expression>? ";" <expression>? ")" <statement>
    """
    cls._consume_current()
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
       <whileStmt> -> "while" "(" <expression> ")" <statement>
    """
    cls._consume_current()
    cls._expect(TokenType.LEFT_PAREN, err_msg = "expected '(' after 'while'")
    condition = cls._expression()
    cls._expect(TokenType.RIGHT_PAREN, err_msg = "expected ')' after condition")

    body = cls._statement()

    # init = None, increment = None
    return ForStmt(None, condition, None, body)

  @classmethod
  def _returnStmt(cls) -> Stmt:    
    """
       <returnStmt> -> "return" <expression>? ";"
    """
    cls._consume_current()
    value = cls._expression() if not cls._match(TokenType.SEMICOLON) else None

    cls._expect(TokenType.SEMICOLON, err_msg = "expected ';' after expression")
  
    return ReturnStmt(value)

  @classmethod
  def _exprStmt(cls) -> Stmt:
    """
       <exprStmt> -> <expression>? ";"
    """
    expr = cls._expression() if not cls._match(TokenType.SEMICOLON) else None

    cls._expect(TokenType.SEMICOLON, err_msg = "expected ';' after expression")
    
    return ExpressionStmt(expr) 

  @classmethod
  def _expression(cls) -> Expr:
    """
       <expression> -> <assignment>
    """
    return cls._assignment()

  @classmethod
  def _assignment(cls) -> Expr:
    """ 
       <assignment> -> <equality> ("=" <assignment>)?
    """
    left = cls._equality()

    if cls._match(TokenType.EQUAL) :

      equals = cls._consume_current()

      if not (left.is_variable or (left.is_unary and left.is_deref)) :  
        # can only cascade variables and dereferences in an assignment
        raise SyntaxErr(equals, "not an lvalue")
      else: 
        right = cls._assignment()
        left = AssignExpr(left, equals, right)
        left.operand_type = cls._add_type(left)

    return left

  @classmethod
  def _equality(cls) -> Expr:
    """
       <equality> -> <comparison> ("==" <comparison> | "!=" <comparison>)*
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
       <comparison> -> <addition> ("<" <addition> | "<=" <addition> | ">" <addition> | ">=" <addition>)*
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
  def _new_add(cls, left : Expr, operator : Token, right : Expr) -> Expr:

    left.operand_type  = cls._add_type(left)
    right.operand_type = cls._add_type(right)

    # num + num
    if left.operand_type.is_integer and right.operand_type.is_integer:
      left = BinaryExpr(left, operator, right)
    
    else:
      # parse pointer arithmetic

      # ptr + ptr, not defined behaviour
      if left.operand_type.is_pointer and right.operand_type.is_pointer:
        raise SyntaxErr(operator, "invalid operands")

      if left.operand_type.is_integer and right.operand_type.is_pointer:
        # convert 'num + ptr' to 'ptr + num'
        left, right = right, left

      # convert 'ptr + num' to 'ptr + (num * sizeof(basetype))'
      mul_op = copy(operator); mul_op.kind = TokenType.STAR
      right = BinaryExpr(right, mul_op, LiteralExpr(left.operand_type.base.size))
      left = BinaryExpr(left, operator, right)

    left.operand_type = cls._add_type(left)
    return left

  @classmethod
  def _new_sub(cls, left : Expr, operator : Token, right : Expr) -> Expr:

    left.operand_type  = cls._add_type(left)
    right.operand_type = cls._add_type(right)

    # num - num
    if left.operand_type.is_integer and right.operand_type.is_integer:
      left = BinaryExpr(left, operator, right)

    else:
      # ptr - num
      if left.operand_type.is_pointer and right.operand_type.is_integer:
        mul_op = copy(operator); mul_op.kind = TokenType.STAR
        right = BinaryExpr(right, mul_op, LiteralExpr(left.operand_type.base.size))
        left = BinaryExpr(left, operator, right)
        
      # ptr - ptr, how many elements are between the two  
      elif left.operand_type.is_pointer and right.operand_type.is_pointer:
        left = BinaryExpr(left, operator, right)
        left.operand_type = ty_int
        div_op = copy(operator); div_op.kind = TokenType.SLASH
        left = BinaryExpr(left, div_op, LiteralExpr(left.operand_type.size))

      else:
        raise SyntaxErr(operator, "invalid operands")

    left.operand_type = cls._add_type(left)
    return left

  @classmethod
  def _addition(cls) -> Expr:
    """
       <addition> -> <multiplication> ("+" <multiplication> | "-" <multiplication>)*
    """
    left = cls._multiplication()
    
    while cls._match(TokenType.PLUS, TokenType.MINUS) :
      operator = cls._consume_current()
      right = cls._multiplication()

      try:
        if operator.kind == TokenType.PLUS :
          left = cls._new_add(left, operator, right)  
        else:
          left = cls._new_sub(left, operator, right)

      except SyntaxErr as err: raise
      
    return left

  @classmethod
  def _multiplication(cls) -> Expr:
    """
       <multiplication> -> <unary> ("*" <unary> | "/" <unary>)*
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
       <unary> -> ("+" | "-" | "&" | "*") <unary> | <postfix>
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

    return cls._postfix()

  @classmethod
  def _postfix(cls) -> Expr:
    """
       <postfix> -> <primary> ("[" <expression> "]")*
    """
    left = cls._primary()

    while cls._match(TokenType.LEFT_BRACKET) :
      operator = cls._consume_current() # consumes '['
      operator.kind = TokenType.STAR # dereference operator
      
      idx = cls._expression()
      
      cls._expect(TokenType.RIGHT_BRACKET, err_msg = "expected ']'")
      
      # x[y] is short for *(x+y) or *(&x + sizeof(basetype) * y)
      add_op = copy(operator); add_op.kind = TokenType.PLUS
      left = cls._new_add(left, add_op, idx)
      left = UnaryExpr(left, operator)
      left.operand_type = cls._add_type(left)

    return left

  @classmethod
  def _resolve_function(cls, fname : Token) -> Fn:
    
    for fn in cls._globals :
      if not fn.is_function : continue
      if fn.name == fname.lexeme : return fn  

    # warning: function undeclared
    raise SyntaxErr(fname, "implicit declaration of function '%s'" %(fname.lexeme), True)

  @classmethod
  def _funcall(cls, fname : Token) -> Expr:
    """
       <funcall> -> IDENTIFIER "(" ( <assignment> ("," <assignment>)*)? ")"
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

    try:
      fn = cls._resolve_function(fname)
    except SyntaxErr as err:
      error_collector.add(err) # non-critical
      # if function not defined, don't try to evaluate arg_list
      return FunCallExpr(fname.lexeme, arg_list)
    else:  
      i = 0 # iterate over the arguments list and check for type mismatches
      while i < min(len(arg_list), fn.arity) :
        try: # report all type mismatches
          if arg_list[i].operand_type != fn.params[i].data_type :
            raise SyntaxErr(fname, "expected '%s' but argument %d is of type '%s'"
                          %(str(fn.params[i].data_type), i+1, str(arg_list[i].operand_type)))
        except SyntaxErr as err :
          error_collector.add(err) # non-critical ?
        finally: i += 1

      try:
        if len(arg_list) < fn.arity :  # critical
          raise SyntaxErr(fname, "too few arguments to function '%s'" %(fname.lexeme))
        elif len(arg_list) > fn.arity :  # critical
          raise SyntaxErr(fname, "too many arguments to function '%s'" %(fname.lexeme))

      except SyntaxErr : raise

      else : return FunCallExpr(fname.lexeme, arg_list)

  @classmethod
  def _find_var(cls, obj_name : Token) :
    
    var_name = obj_name.lexeme

    if var_name in cls._locals : # try to find as a local variable
      return cls._locals[var_name]
    else:
      for obj in cls._globals : # try to find as a global variable
        if not obj.is_function and obj.name == var_name : 
          return obj
      
      raise SyntaxErr(obj_name, "%s undeclared" %(var_name)) 

  @classmethod
  def _primary(cls) -> Expr:
    """
       <primary> -> NUMBER | IDENTIFIER | <funcall> | "sizeof" <unary> | "(" <expression> ")"
    """
    if cls._match(TokenType.NUM) :
      curr_token = cls._consume_current()
      return LiteralExpr(curr_token.literal)

    elif cls._match(TokenType.IDENTIFIER) :

      obj_name = cls._consume_current()

      if cls._match(TokenType.LEFT_PAREN) :
        return cls._funcall(obj_name)

      else :
        # variable
        var_desc = cls._find_var(obj_name)
        left = VariableExpr(var_desc)
        left.operand_type = var_desc.data_type
        return left

    elif cls._match(TokenType.SIZEOF) :
      cls._consume_current()
      expr = cls._unary() # parse and add type to operand
      return LiteralExpr(expr.operand_type.size)

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
      return cls._consume_current()
    else:
      raise SyntaxErr(cls._peek(), err_msg)
    
  @classmethod
  def _syncronize(cls, e_brace : int = 0) -> None :
    # enter in panic mode
    # discard tokens until a valid statement or expression is found

    if e_brace : # panicked at function definition
      
      while not cls._is_at_end() :
        tk = cls._consume_current()

        if tk.kind == TokenType.RIGHT_BRACE :
          if e_brace == 1 : break
          else : e_brace -= 1

        elif tk.kind == TokenType.LEFT_BRACE :
          e_brace += 1

    else : # panicked inside some function

      while not cls._is_at_end() :
        if cls._previous().kind in {
          TokenType.SEMICOLON, 
          TokenType.RIGHT_BRACE
        } : return # end of a statement

        elif cls._peek().kind in {
          TokenType.IF, TokenType.INT,
          TokenType.FOR, TokenType.LEFT_BRACE,
          TokenType.RETURN, TokenType.WHILE
        } : return # beginning of a statement
        
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
      

