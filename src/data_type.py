
class DataType:

  def __init__(self) :
    self.size = 0

  @property
  def is_integer(self) :
    return isinstance(self, Int)
  
  @property
  def is_pointer(self) :
    return isinstance(self, Pointer_to)

  @property
  def is_array(self) :
    return isinstance(self, Array_of)

  def __eq__(self, other) :
    return type(self) is type(other)

class Int (DataType):
  def __init__(self) :
    self.size = 8 # don't differentiate for now

  def __str__(self) :
    return "int"

class Pointer_to (DataType):
  def __init__(self, base : DataType) :
    self.base = base
    self.size = 8

  def __eq__(self, other) :
    if not other.is_pointer : return False
    # evaluates equality recursively
    return self.base == other.base 

  def __str__(self) :
    return str(self.base) + "*"

class Array_of (Pointer_to) :
  def __init__(self, base : DataType, size : int) :
    super().__init__(base)
    self.length = size
    self.size = base.size * self.length

class Function_type (DataType):
  def __init__(self, ret_type : DataType) :
    self.ret_type = ret_type

ty_int = Int()

