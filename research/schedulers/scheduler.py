from abc import ABC, abstractmethod
from typing import Dict, Union
from collections import deque

from wfcommons import common, wfinstances

Id = Union[str, int]
Task = common.Task
Instance = wfinstances.Instance
Workflow = common.Workflow

class Processor(common.Machine):
  available_at: float

class Scheduler(ABC):
  @abstractmethod
  def schedule(
    self,
    ready_tasks: deque,
    processors: Dict[str, Processor],
    completed_tasks: Dict[str, float],
    workflow: Workflow
  ) -> tuple[int, str, float]:
    pass
