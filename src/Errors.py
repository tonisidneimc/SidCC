import sys

from .Token import *

class ErrorCollector :
  def __init__(self) :
    self.issues = []
	
  def add(self, issue : Exception) :
    self.issues.append(issue)
	
  def ok(self) :
    # if no error (warning=False) occurred
    return not any(not issue.warning for issue in self.issues) 
	
  def show(self) :
    for issue in self.issues :
      print(issue, file=sys.stderr)

  def clear(self) :
    self.issues = []

error_collector = ErrorCollector()

class ScanError(Exception) :
  def __init__(self, message : str, row : int, col : int, full_line : str) :	
    self.message = message
    self.row = row
    self.col = col
    self.full_line = full_line
    self.warning = False
    
  def __str__(self) :

    where = str(self.row) + ":" + str(self.col)
    indicator = " " * (self.col) + "^"
    return f"{where}: error: {self.message}\n  {self.full_line}\n  {indicator}"

class CompileError(Exception) :
  def __init__(self, token : Token, message : str, full_line : str, warning=False) :
    self.message = message
    self.tk_info = token
    self.full_line = full_line
    self.warning = warning
	
  def __str__(self) :
    where = str(self.tk_info.row) + ":" + str(self.tk_info.col)
    issue_type = "warning" if self.warning else "error"		
    indicator = " " * (self.tk_info.col) + "^"
    return f"{where}: {issue_type}: {self.message}\n  {self.full_line}\n  {indicator}"
  

