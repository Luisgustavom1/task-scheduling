from typing import Dict
from collections import deque

from schedulers.scheduler import Scheduler, Workflow, Processor

class FIFOScheduler(Scheduler):
  def __init__(self):
    self.name = "FIFO"

  def schedule(
    self,
    ready_tasks: deque,
    processors: Dict[str, Processor],
    completed_tasks: Dict[str, float],
    workflow: Workflow
  ) -> tuple[int, str, float]:
    task_id = ready_tasks.popleft()
    
    best_processor = min(processors, key=lambda p: processors[p].available_at)
    
    parents: Dict[str, set[str]] = workflow.tasks_parents[task_id]
    task_ready_time = 0
    if parents:
      task_ready_time = max(completed_tasks[p_id] for p_id in parents)
        
    return task_id, best_processor, task_ready_time