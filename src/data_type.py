
class DataType:
  def __init__(self) : pass

  @property
  def is_integer(self) :
    return isinstance(self, Int)
  
  @property
  def is_pointer(self) :
    return isinstance(self, Pointer_to)

  def __eq__(self, other) :
    return type(self) is type(other)

class Int(DataType):
  def __init__(self) : pass

  def __str__(self) :
    return "int"

class Pointer_to(DataType):
  def __init__(self, base : DataType) :
    self.base = base

  def __eq__(self, other) :
    if not other.is_pointer : return False
    # evaluates equality recursively
    return self.base == other.base 

  def __str__(self) :
    return str(self.base) + "*"

class Function(DataType):
  def __init__(self, ret_type : DataType) :
    self.ret_type = ret_type

ty_int = Int()

