import sys

from .token import *

bold_color = "\033[1m"
error_color = "\x1B[31m"
warning_color = "\x1B[33m"    
reset_color = "\x1B[0m"

class CompilerError(Exception) :
  def __init__(self, msg : str, row : int, col : int, warning : bool=False):
    self.message = msg
    self.warning = warning
    self.row = row
    self.col = col
  
  def __str__(self) : pass

class ScanError(CompilerError) :
  def __init__(self, message : str, row : int, col : int) :	
    super().__init__(message, row, col)
    
  def __str__(self) -> str:

    where = str(self.row) + ':' + str(self.col+1)		
    
    return f"{bold_color}{where}:{error_color} error:{reset_color} {self.message}\n"

class ParseError(CompilerError) :
  def __init__(self, tk_info : Token, message : str, warning : bool=False) :
    super().__init__(message, tk_info.row, tk_info.col, warning)

  def __str__(self) -> str:

    where = str(self.row) + ':' + str(self.col+1)

    issue_color = warning_color if self.warning else error_color
    issue_type = "warning" if self.warning else "error"    

    return f"{bold_color}{where}: {issue_color}{issue_type}:{reset_color} {self.message}\n"


class ErrorCollector :
  def __init__(self) :
    self.issues = []
    self.source = []	

  def set_source(self, source : str) :
    self.source = source.split('\n')

  def add(self, issue : CompilerError) :
    self.issues.append(issue)
	
  def ok(self) :
    # if no error (warning=False) occurred
    return not any(not issue.warning for issue in self.issues) 
	
  def show(self) :

    for issue in self.issues :

      issue_color = warning_color if issue.warning else error_color
      indicator = ' ' * (issue.col + 4) + bold_color + issue_color + '^' + reset_color

      err_out = str(issue) + (' ' * 4) + self.source[issue.row - 1] + '\n' + indicator

      print(err_out, file=sys.stderr)

  def clear(self) :
    self.issues = []

error_collector = ErrorCollector()


