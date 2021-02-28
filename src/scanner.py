from .token import *
from .token_type import *
from .errors import ScanError, error_collector

__all__ = ["Scanner"]

class Scanner(object) : 

  # C reserved keywords
  _keywords = {
    "if"     : TokenType.IF,
    "else"   : TokenType.ELSE,
    "return" : TokenType.RETURN,
  }

  # punctuators characters
  _punct = {
    '('  : (lambda : Scanner._make_token(TokenType.LEFT_PAREN)),
    ')'  : (lambda : Scanner._make_token(TokenType.RIGHT_PAREN)),
    '{'  : (lambda : Scanner._make_token(TokenType.LEFT_BRACE)),
    '}'  : (lambda : Scanner._make_token(TokenType.RIGHT_BRACE)),
    ';'  : (lambda : Scanner._make_token(TokenType.SEMICOLON)),
    '-'  : (lambda : Scanner._make_token(TokenType.MINUS)),
    '+'  : (lambda : Scanner._make_token(TokenType.PLUS)),
    '*'  : (lambda : Scanner._make_token(TokenType.STAR)),
    '/'  : (lambda : Scanner._make_token(TokenType.SLASH)),
    '!'  : (lambda : Scanner._make_token(TokenType.BANG_EQUAL if Scanner._match("=") else TokenType.BANG)),
    '='  : (lambda : Scanner._make_token(TokenType.EQUAL_EQUAL if Scanner._match('=') else TokenType.EQUAL)),
    '>'  : (lambda : Scanner._make_token(TokenType.GREATER_EQUAL if Scanner._match('=') else TokenType.GREATER)),
    '<'  : (lambda : Scanner._make_token(TokenType.LESS_EQUAL if Scanner._match('=') else TokenType.LESS))
  }

  @classmethod
  def tokenize(cls, source : str) -> list:	
    
    cls._source = source  # character buffer to be tokenized
    cls._start = 0        # works as a pointer to the beginning of a token 
    cls._current = 0      # works as a pointer to the end of a token              
    cls._line = 1

    tk_list = []
    	
    while not cls._eof() :                
      try :			
        token = cls._scan_token()
      except ScanError as err :
        error_collector.add(err)	
      else :
        tk_list.append(token)
    
    cls._start = cls._current     
    tk_list.append(cls._make_token(TokenType.EOF))
        
    return tk_list  
      
  @classmethod
  def _scan_token(cls) -> Token:
    cls._skipws()
    
    if cls._eof() : 
      return cls._make_token(TokenType.EOF)

    cls._start = cls._current
        
    c = cls._advance()
    
    if c in cls._punct :
      return cls._punct[c]()
        
    elif str.isdigit(c) : 
      return cls._number()

    elif cls._is_ident(c):
      return cls._identifier() 
    
    else : 
      raise ScanError(f"unexpected character '{c}'", cls._line, cls._current - 1)
            
  @classmethod
  def _make_token(cls, kind : TokenType, literal : object = None) -> Token :
    # creates a token, with lexeme at _source from _start until _current - 1

    lexeme = cls._source[cls._start : cls._current]
    return Token(kind, lexeme, literal, cls._line, cls._start)
  
  @classmethod          
  def _number(cls) -> Token :

    while str.isdigit(cls._peek()) :
      cls._current += 1
      	
    return cls._make_token(TokenType.NUM, int(cls._source[cls._start : cls._current]))

  @staticmethod
  def _is_ident(c : str) -> bool:

    return str.isalnum(c) or c == '_'  

  @classmethod
  def _identifier(cls) -> Token :

    while cls._is_ident(cls._peek()) :
      cls._current += 1

    lexeme = cls._source[cls._start : cls._current]

    if lexeme not in cls._keywords : 
      return cls._make_token(TokenType.IDENTIFIER, lexeme)
    else :
      return cls._make_token(cls._keywords[lexeme])    

  @classmethod
  def _eof(cls) -> bool :
    # checks if there is any character still to be processed from the buffer
    return cls._current >= len(cls._source)

  @classmethod
  def _match(cls, expected : str) -> bool :

    if cls._peek() != expected : return False

    cls._current += 1
    return True
  
  @classmethod
  def _advance(cls, offset : int = 1) -> str :    
    
    if cls._eof() : return ''
        
    cls._current += offset
    return cls._source[cls._current - offset]
    
  @classmethod
  def _peek(cls) -> str:
    # get the current character in the buffer
    if cls._eof() : return '\0'
    
    return cls._source[cls._current]

  @classmethod        
  def _skipws(cls) -> None :
    	
    while not cls._eof() :
      c = cls._peek()
            
      if c not in {' ', '\n', '\r', '\t'} : 
        break
        		
      cls._current += 1

