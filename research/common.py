from typing import Union
from wfcommons import common, wfinstances

Id = Union[str, int]
Task = common.Task
Workflow = common.Workflow
Instance = wfinstances.Instance

class Processor(common.Machine):
  available_at: float