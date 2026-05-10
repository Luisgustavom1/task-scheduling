from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Union

from common import Id, Resource

from wfcommons import wfinstances

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

@dataclass
class ScheduleTaskOnCores:
  task: int
  resource: int
  cores: List[int]
  expected_span: Optional[TimeSpan] = None

@dataclass
class TransferData:
  data_item: int
  source: Id
  target: Id

Action = Union[ScheduleTask, ScheduleTaskOnCores, TransferData]

class Scheduler(ABC):
  @abstractmethod
  def start(self, dag: wfinstances.Instance, resources: List[Resource]) -> List[Action]:
      pass