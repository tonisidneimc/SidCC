from .token import *
from .token_type import *
from .errors import ScanError, error_collector

__all__ = ["Scanner"]

class Scanner(object) :
    
  def __init__(self, source : str) :
    self._start = 0         # works as a pointer to the beginning of a token 
    self._current = 0       # works as a pointer to the end of a token
    self._source = source   # character buffer to be tokenized       
    self._line = 1
	
    # punctuators characters
    self.punct = {
      '('  : (lambda : self._make_token(TokenType.LEFT_PAREN)),
      ')'  : (lambda : self._make_token(TokenType.RIGHT_PAREN)),
      '-'  : (lambda : self._make_token(TokenType.MINUS)),
      '+'  : (lambda : self._make_token(TokenType.PLUS)),
      '*'  : (lambda : self._make_token(TokenType.STAR)),
      '/'  : (lambda : self._make_token(TokenType.SLASH)),
      '!'  : (lambda : self._make_token(TokenType.BANG_EQUAL if self._match("=") else TokenType.BANG)),
      '='  : (lambda : self._make_token(TokenType.EQUAL_EQUAL if self._match('=') else TokenType.EQUAL)),
      '>'  : (lambda : self._make_token(TokenType.GREATER_EQUAL if self._match('=') else TokenType.GREATER)),
      '<'  : (lambda : self._make_token(TokenType.LESS_EQUAL if self._match('=') else TokenType.LESS))
    }
    
  def tokenize(self) -> list:	
    
    tk_list = []
    	
    while not self._eof() :                
      try :			
        token = self._scan_token()
      except ScanError as err :
        error_collector.add(err)	
      else :
        tk_list.append(token)
    
    self._start = self._current     
    tk_list.append(self._make_token(TokenType.EOF))
        
    return tk_list
        
  def _scan_token(self) -> Token:
    self._skipws()
    
    if self._eof() : 
      return self._make_token(TokenType.EOF)

    self._start = self._current
        
    c = self._advance()
    
    if c in self.punct :
      return self.punct[c]()
        
    elif str.isdigit(c) : 
      return self._number()
        
    else : 
      raise ScanError(f"Unexpected character '{c}'", self._line, self._current-1)
            
  def _make_token(self, kind : TokenType, literal : object = None) -> Token :
    # creates a token, with lexeme at _source from _start until _current - 1

    lexeme = self._source[self._start : self._current]
    return Token(kind, lexeme, literal, self._line, self._start)
            
  def _number(self) -> None :

    while str.isdigit(self._peek()) :
      self._current += 1
      	
    return self._make_token(TokenType.NUM, int(self._source[self._start : self._current]))
		
  def _eof(self) -> bool :
    # checks if there is any character still to be processed from the buffer
    return self._current >= len(self._source)

  def _match(self, expected : str) -> bool :

    if self._peek() != expected : return False

    self._current += 1
    return True
  
  def _advance(self, offset : int = 1) -> str :    
    
    if self._eof() : return ''
        
    self._current += offset
    return self._source[self._current - offset]
    
  def _peek(self) -> str:
    # get the current character in the buffer
    if self._eof() : return '\0'
    
    return self._source[self._current]
        
  def _skipws(self) -> None :
    	
    while not self._eof() :
      c = self._peek()
            
      if c not in {' ', '\n', '\r', '\t'} : 
        break
        		
      self._current += 1

