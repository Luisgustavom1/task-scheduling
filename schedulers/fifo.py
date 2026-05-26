from typing import Dict

from schedulers.scheduler import Scheduler
from simulator import Simulator

class FIFOScheduler(Scheduler):
  def __init__(self, sim: Simulator):
    self.name = "FIFO"
    self.sim = sim

  def schedule(self) -> tuple[str, str]:
    processors = self.sim.processors

    task_id = self.sim.ready_tasks.popleft()
    
    best_processor = min(processors, key=lambda p: processors[p].available_at)

    return task_id, best_processor