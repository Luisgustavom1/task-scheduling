from abc import ABC, abstractmethod
from typing import Union

from wfcommons import common, wfinstances

Id = Union[str, int]
Task = common.Task
Instance = wfinstances.Instance
Workflow = common.Workflow

class Processor(common.Machine):
  pass

class Scheduler(ABC):
  insertion_based_policy: bool = True

  @abstractmethod
  def schedule(self) -> tuple[str, str]:
    pass
