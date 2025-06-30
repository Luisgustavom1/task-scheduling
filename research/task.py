from enum import Enum, auto
from typing import Optional, Set, List
from dataclasses import dataclass, field

class TaskState(Enum):
  PENDING      # Waiting for its dependencies
  READY        # All dependencies are satisfied, ready to be scheduled
  SCHEDULED    # Task is scheduled, waiting for its dependencies
  RUNNABLE     # All dependencies are satisfied and task is scheduled
  RUNNING      # Task is running
  DONE         # Task is completed

@dataclass
class Task:
  name: str
  flops: float  # The amount of computations performed by this task in Gflops
  memory: int   # Memory in MB
  min_cores: int
  max_cores: int
  cores_dependency: object
  state: TaskState = TaskState.READY
  inputs: List[int] = field(default_factory=list)
  outputs: List[int] = field(default_factory=list)
  ready_inputs: int = field(default=0, init=False)
  resource_restriction: Optional[ResourceRestriction] = None

  @classmethod
  def new(cls, name, flops, memory, min_cores, max_cores, cores_dependency):
    return cls(
      name=name,
      flops=flops,
      memory=memory,
      min_cores=min_cores,
      max_cores=max_cores,
      cores_dependency=cores_dependency,
      state=TaskState.READY,
      resource_restriction=None
    )