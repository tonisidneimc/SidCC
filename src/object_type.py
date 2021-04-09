
class Object : # for Variable/Function description
  def __init__(self, data_type, name : str) :
    self.data_type = data_type
    self.name = name

  @property
  def is_function(self) -> bool:
    return isinstance(self, Fn)

class Var(Object) :
  def __init__(self, data_type, name : str) :
    super().__init__(data_type, name)

  @property
  def is_local(self) -> bool:
    return isinstance(self, LVar)

class GVar(Var) :
  def __init__(self, data_type, name : str) :
    super().__init__(data_type, name)

class LVar(Var) :
  def __init__(self, data_type, offset : int) :
    # doesn't need of the name to describe a local variable 
    # only their offset from RBP is enough
    super().__init__(data_type, "")
    self.offset = offset

class Fn(Object) :
  def __init__(self, fname : str, ret_type, params, body, lvars, stack_size) :
    super().__init__(ret_type, fname)
    self.params = params # a list of parameters
    self.arity = len(self.params)
    self.stack_size = stack_size
    self.lvars = lvars # a dict of local variables
    self.body = body # a list of statements

