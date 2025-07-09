from dataclasses import dataclass

from common import Id

@dataclass
class Resource:
  id: Id
  name: str
  speed: float  # Gflop/s
  cores: int
  cores_available: int
  memory: int  # MB
  memory_available: int