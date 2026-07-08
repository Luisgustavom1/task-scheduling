from typing import Dict
from schedulers.scheduler import Scheduler, Task
from simulator import Simulator

class PEFT(Scheduler):
  def __init__(self, simulator: Simulator):
    self.name = "PEFT"
    self.sim = simulator
    self._rank_oct: Dict[str, float] = {}
    self._oct_table: Dict[str, Dict[str, float]] = {}

  def schedule(self) -> tuple[str, str]:
    if not self._rank_oct:
      for task_id in self.sim.workflow.tasks:
        self.rank_oct(task_id)

    # tasks with all parents completed and not yet scheduled
    unescheduled_tasks = [
      self.sim.workflow.tasks[tid] for tid in self.sim.ready_tasks
      if tid not in self.sim.completed_tasks
    ]

    selected_task = max(unescheduled_tasks, key=lambda t: self._rank_oct[t.task_id])
    task_id = selected_task.task_id

    best_processor = None
    min_optimistic_eft = float('inf')

    for pj in self.sim.processors:
      optimistic_eft = self.sim.calc_eft(task_id, pj) + self.calc_oct(task_id, pj)

      if optimistic_eft < min_optimistic_eft:
        min_optimistic_eft = optimistic_eft
        best_processor = pj

    if best_processor is None:
      raise RuntimeError(f"Unable to select processors for task {task_id}.")

    return task_id, best_processor

  def rank_oct(self, ti: str) -> float:
    if ti in self._rank_oct:
      return self._rank_oct[ti]

    oct_sum = sum(self.calc_oct(ti, pk) for pk in self.sim.processors)

    self._rank_oct[ti] = oct_sum / len(self.sim.processors) if self.sim.processors else 0

    return self._rank_oct[ti]
  
  def calc_oct(self, ti: str, pk: str) -> float:
    if ti in self._oct_table and pk in self._oct_table[ti]:
      return self._oct_table[ti][pk]

    max_oct = 0
    for tj in self.sim.workflow.tasks_children[ti]:
      min_oct = float('inf')
      for pw in self.sim.processors:
        communication_cost = 0 if pw == pk else self.sim.calc_communication_cost(ti, tj)
        oct_val = self.calc_oct(tj, pw) + self.sim.execution_cost[tj].get(pw, 0) + communication_cost
        min_oct = min(min_oct, oct_val)

      max_oct = max(max_oct, min_oct)

    if ti not in self._oct_table:
      self._oct_table[ti] = {}
    self._oct_table[ti][pk] = max_oct

    return max_oct