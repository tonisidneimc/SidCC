
class DataType:
  def __init__(self) : pass

  @property
  def is_integer(self) :
    return isinstance(self, Int)
  
  @property
  def is_pointer(self) :
    return isinstance(self, Pointer_to)

class Int(DataType):
  def __init__(self) : pass

class Pointer_to(DataType):
  def __init__(self, base : DataType) :
    self.base = base

class Function(DataType):
  def __init__(self, ret_type : DataType) :
    self.ret_type = ret_type

ty_int = Int()

