from enum import Enum, auto
from typing import List
from dataclasses import dataclass, field

class TaskState(Enum):
  PENDING = auto()      # Waiting for its dependencies
  READY = auto()        # All dependencies are satisfied, ready to be scheduled
  SCHEDULED = auto()    # Task is scheduled, waiting for its dependencies
  RUNNABLE = auto()     # All dependencies are satisfied and task is scheduled
  RUNNING = auto()      # Task is running
  DONE = auto()         # Task is completed

@dataclass
class Task:
  name: str
  flops: float  # The amount of computations performed by this task in Gflops
  memory: float   # Memory in MB
  min_cores: int
  max_cores: int
  state: TaskState = TaskState.READY
  inputs: List[int] = field(default_factory=list)
  outputs: List[int] = field(default_factory=list)
  ready_inputs: int = field(default=0, init=False)
  # TODO: Uncomment when ResourceRestriction is defined
  # resource_restriction: Optional[ResourceRestriction] = None

  @classmethod
  def new(cls, name, flops, memory, min_cores, max_cores):
    return cls(
      name=name,
      flops=flops,
      memory=memory,
      min_cores=min_cores,
      max_cores=max_cores,
      state=TaskState.READY,
      # resource_restriction=None
    )