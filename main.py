import sys

from src.scanner import Scanner
from src.parser import Parser
from src.asm_gen import Asm_Generator
from src.errors import error_collector

if __name__ == "__main__" :

  if len(sys.argv) != 2 :
    sys.stderr.write("%s: invalid number of arguments" %(sys.argv[0]))
    sys.exit(64)

  user_input = sys.argv[1] 
  
  error_collector.set_source(user_input)

  tk_list = Scanner.tokenize(user_input)

  # for token in tk_list :
  #  print(token)
  
  error_collector.show()	
  if not error_collector.ok() :
    sys.exit(1)

  prog = Parser.parse(tk_list)

  error_collector.show()	
  if not error_collector.ok() :
    sys.exit(1)

  Asm_Generator.gen(prog)
	


