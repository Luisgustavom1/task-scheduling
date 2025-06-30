from enum import Enum
from typing import Optional, List

class DataItemState(Enum):
  PENDING = "Pending"
  READY = "Ready"

class DataItem:
  def __init__(
    self,
    name: str,
    size: float,  # MB
    state: DataItemState = DataItemState.PENDING,
    producer: Optional[int] = None
  ):
    self.name: str = name
    self.size: float = size
    self.producer: Optional[int] = producer
    self.consumers: List[int] = []
    self.state: DataItemState = state

  @classmethod
  def new(cls, name: str, size: float, state: DataItemState, producer: Optional[int] = None):
    return cls(name, size, state, producer)