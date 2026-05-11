from abc import ABC, abstractmethod
from typing import Union

from wfcommons import common, wfinstances

Id = Union[str, int]
Task = common.Task
Instance = wfinstances.Instance
Workflow = common.Workflow

class Processor(common.Machine):
  available_at: float

class Scheduler(ABC):
  @abstractmethod
  def schedule(self) -> tuple[int, str, float]:
    pass
