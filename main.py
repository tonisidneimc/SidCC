import sys

from src.Scanner import *
from src.Token import *
from src.TokenType import *
from src.Errors import CompileError, error_collector

if __name__ == "__main__" :

  if len(sys.argv) != 2 :
    sys.stderr.write("%s: invalid number of arguments" %(sys.argv[0]))
    sys.exit(64)

  scanner = Scanner(sys.argv[1])
  tk_list = scanner.tokenize()
	
  error_collector.show()	
  if not error_collector.ok() :
    sys.exit(1)

  out = """.text
  .globl main
  main:
    pushq %rbp
    movq %rsp, %rbp\n"""
	
  token = tk_list[0]

  if token.kind == TokenType.EOF :
    sys.exit(1)

  if token.kind == TokenType.NUM :
    out += " " * 4 + "movq $%d, %%rax\n" %(token.literal)	

  try:
    i = 1
    while True :			
      token = tk_list[i]
			
      if token.kind == TokenType.EOF : break

      if token.kind == TokenType.NUM : 
        raise CompileError(token, "expected an operator", sys.argv[1]) 

      elif token.kind == TokenType.PLUS :
				
        if tk_list[i+1].kind != TokenType.NUM : 
          raise CompileError(tk_list[i+1], "expected a number", sys.argv[1])
				
        out += " " * 4 + "addq $%d, %%rax\n" %(tk_list[i+1].literal)
			
      elif tk_list[i].kind == TokenType.MINUS : 	
        if tk_list[i+1].kind != TokenType.NUM : 
          raise CompileError(tk_list[i+1], "expected a number", sys.argv[1])	
							
        out += " " * 4 + "subq $%d, %%rax\n" %(tk_list[i+1].literal)
	
      i += 2	
  except CompileError as err :
    print(err, file=sys.stderr)
    sys.exit(1)
	
  else:
    out += " " * 4 + "leave\n"
    out += " " * 4 + "ret\n"
		
    print(out)
	
