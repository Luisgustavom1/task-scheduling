from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, Union
from collections import deque

from common import Processor, Workflow

@dataclass
class TimeSpan:
  start: float
  finish: float

  def length(self) -> float:
    return self.finish - self.start

@dataclass
class ScheduleTask:
  task: int
  resource: int
  cores: int
  expected_span: Optional[TimeSpan] = None


Action = Union[ScheduleTask]

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