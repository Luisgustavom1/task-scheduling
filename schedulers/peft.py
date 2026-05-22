from typing import Dict
from schedulers.scheduler import Scheduler, Task
from simulator import Simulator

class PEFT(Scheduler):
  def __init__(self, simulator: Simulator):
    self.name = "PEFT"
    self.sim = simulator
    self.oct_table: Dict[str, float] = {}

  def schedule(self) -> tuple[str, str, float]:
    if not self.oct_table:
      for task_id in self.sim.workflow.tasks:
        self.calc_rank_oct(task_id)

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
      optimistic_eft = self.calc_eft(task_id, pj) + self.calc_oct(task_id, pj)

      if optimistic_eft < min_optimistic_eft:
        min_optimistic_eft = optimistic_eft
        best_processor = pj

    return task_id, best_processor, self.calc_est(task_id, best_processor)

  def calc_eft(self, ti: str, pj: str) -> float:
    est = self.calc_est(ti, pj)
    execution_time = self.sim.execution_cost[ti].get(pj, 0)
    return est + execution_time

  def calc_est(self, ni: str, pj: str) -> float:
    data_ready_time = max(
      self.calc_aft(nm) + self.sim.calc_communication_cost(nm, ni, pj)
      for nm in self.sim.workflow.tasks_parents[ni]
    ) if self.sim.workflow.tasks_parents[ni] else 0

    return max(self.sim.processors[pj].available_at, data_ready_time)
  
  def calc_aft(self, ni: str) -> float:
    aft = self.sim.completed_tasks[ni]
    if aft is None:
      raise ValueError(f"task {ni} has not been completed yet.")
    return aft

  def calc_rank_oct(self, ti: str) -> float:
    if ti in self.oct_table:
      return self.oct_table[ti]

    sum = 0
    for pk in self.sim.processors:
      sum += self.calc_oct(ti, pk)

    self.oct_table[ti] = sum / len(self.sim.processors) if self.sim.processors else 0

    return self.oct_table[ti]
  
  def calc_oct(self, ti: str, pk: str) -> float:
    max_oct = 0
    for tj in self.sim.workflow.tasks_children[ti]:
      min_oct = float('inf')
      for pw in self.sim.processors:
        communication_cost = 0 if pw == pk else self.sim.communication_cost[ti].get(tj, 0)
        oct = self.calc_rank_oct(tj) + self.sim.execution_cost[tj].get(pw, 0) + communication_cost
        min_oct = min(min_oct, oct)

      max_oct = max(max_oct, min_oct)

    return max_oct