from typing import Dict
from schedulers.scheduler import Scheduler, Task
from simulator import Simulator

class PEFT(Scheduler):
  def __init__(self, simulator: Simulator):
    self.name = "PEFT"
    self.sim = simulator
    self.oct_table: Dict[str, float] = {}

  def schedule(self) -> tuple[str, str]:
    if not self.oct_table:
      for task_id in self.sim.workflow.tasks:
        self.rank_oct(task_id)

    # tasks with all parents completed and not yet scheduled
    unescheduled_tasks = [
      self.sim.workflow.tasks[tid] for tid in self.sim.workflow.tasks 
      if tid not in self.sim.completed_tasks and 
      all(p in self.sim.completed_tasks for p in self.sim.workflow.tasks_parents[tid])
    ]

    # select task with highest upward rank
    selected_task = max(unescheduled_tasks, key=lambda t: self.oct_table[t.task_id])
    task_id = selected_task.task_id

    best_processor = list(self.sim.processors.keys())[0]
    min_optimistic_eft = float('inf')

    for pj in self.sim.processors:
      optimistic_eft = self.sim.calc_eft(task_id, pj) + self.calc_oct(task_id, pj)

      if optimistic_eft < min_optimistic_eft:
        min_optimistic_eft = optimistic_eft
        best_processor = pj

    return task_id, best_processor
  
  def calc_aft(self, ni: str) -> float:
    aft = self.sim.completed_tasks[ni]
    if aft is None:
      raise ValueError(f"task {ni} has not been completed yet.")
    return aft

  def rank_oct(self, ti: str) -> float:
    if ti in self.oct_table:
      return self.oct_table[ti]

    oct_sum = sum(self.calc_oct(ti, pk) for pk in self.sim.processors)

    self.oct_table[ti] = oct_sum / len(self.sim.processors) if self.sim.processors else 0

    return self.oct_table[ti]
  
  def calc_oct(self, ti: str, pk: str) -> float:
    max_oct = 0
    for tj in self.sim.workflow.tasks_children[ti]:
      min_oct = float('inf')
      for pw in self.sim.processors:
        communication_cost = 0 if pw == pk else self.sim.calc_communication_cost(ti, tj)
        oct = self.rank_oct(tj) + self.sim.execution_cost[tj].get(pw, 0) + communication_cost
        min_oct = min(min_oct, oct)

      max_oct = max(max_oct, min_oct)

    return max_oct