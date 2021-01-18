from .Token import *
from .TokenType import *
from .Errors import ScanError, error_collector

__all__ = ["Scanner"]

class Scanner(object) :
    
  def __init__(self, source : str) :
    self._start = 0         # works as a pointer to the beginning of a token 
    self._current = 0       # works as a pointer to the end of a token
    self._source = source   # character buffer to be tokenized
    self._tokens = []       
    self._line = 1
	
    # punctuators characters
    self.punct = {
      "-"  : (lambda : self._addToken(TokenType.MINUS)),
      "+"  : (lambda : self._addToken(TokenType.PLUS))
    }
    
  def tokenize(self) -> list:	
		
    while not self._eof() :                
      try :			
        self._scanToken()
        
      except ScanError as err :
        error_collector.add(err)		

    self._start = self._current     
    self._addToken(TokenType.EOF)
        
    return self._tokens
        
  def _scanToken(self) -> None:
    self._skipws() 

    if self._eof() : return
    self._start = self._current
        
    c = self._advance()
    
    if c in self.punct :
      return self.punct[c]()
        
    elif str.isdigit(c) : 
      return self._number()
        
    else : 
      raise ScanError(f"Unexpected character '{c}'", 
        self._line, self._current, self._source)
            
  def _addToken(self, kind : TokenType, literal : object = None) -> None :
    # creates a token, with lexeme at _source from _start until _current - 1

    lexeme = self._source[self._start : self._current]
    self._tokens.append(Token(kind, lexeme, literal, self._line, self._start))
            
  def _number(self) -> None :
    while str.isdigit(self._peek()) :
      self._advance()
      	
    self._addToken(TokenType.NUM, int(self._source[self._start : self._current]))
		
  def _eof(self) -> bool :
    # checks if there is any character still to be processed from the buffer
    return self._current >= len(self._source)
    
  def _advance(self, offset : int = 1) -> str :    
    if self._eof() : return ""
        
    self._current += offset
    return self._source[self._current - offset]
    
  def _peek(self) -> str:
    # get the current character in the buffer
        
    if self._eof() : return "\0"
    else : 
      return self._source[self._current]
        
  def _skipws(self) -> None :
    	
    while not self._eof() :
      c = self._peek()
            
      if c not in {" ", "\n", "\r", "\t"} : 
        break
        		
      self._advance()

