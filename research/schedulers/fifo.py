from typing import Dict

from schedulers.scheduler import Scheduler
from simulator import Simulator

class FIFOScheduler(Scheduler):
  def __init__(self, sim: Simulator):
    self.name = "FIFO"
    self.sim = sim

  def schedule(self) -> tuple[int, str, float]:
    processors = self.sim.processors

    task_id = self.sim.ready_tasks.popleft()
    
    best_processor = min(processors, key=lambda p: processors[p].available_at)
    
    parents: Dict[str, set[str]] = self.sim.workflow.tasks_parents[task_id]
    task_ready_time = 0
    if parents:
      task_ready_time = max(self.sim.completed_tasks[p_id] for p_id in parents)
        
    return task_id, best_processor, task_ready_time