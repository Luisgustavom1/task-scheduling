from typing import List
from research.resource import Resource
from research.scheduler import Scheduler
from research.workflow import Workflow


class SimpleScheduler(Scheduler):
  def start(self, workflow: Workflow, resources: List[Resource]):
    return