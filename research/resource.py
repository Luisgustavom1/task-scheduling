from dataclasses import dataclass, field
from typing import Any
from copy import deepcopy


@dataclass
class Resource:
  id: str
  name: str
  speed: float  # Gflop/s
  cores: int
  cores_available: int
  memory: int  # MB
  memory_available: int