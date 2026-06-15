import random
from typing import Dict
from schedulers.scheduler import Scheduler, Task
from simulator import Simulator

class IHEFT(Scheduler):
  def __init__(self, simulator: Simulator):
    self.name = "IHEFT"
    self.sim = simulator
    self._rank_proposed: Dict[str, float] = {}
    self._weight_cache: Dict[str, float] = {}

  def schedule(self) -> tuple[str, str]:
    if not self._rank_proposed:
      for task_id in self.sim.workflow.tasks:
        self.rank_proposed(task_id)

    unescheduled_tasks = list(self.sim.ready_tasks)

    if not unescheduled_tasks:
      raise RuntimeError("No unscheduled tasks remaining.")

    unescheduled_tasks.sort(key=lambda tid: (
      -self._rank_proposed[tid],                       # 1. Highest rank first (Descending)
      self.sim.workflow.tasks[tid].priority,         # 2. Lowest priority first (Ascending)
    ))

    task_id = unescheduled_tasks.pop(0)

    self.sim.ready_tasks.remove(task_id)

    best_eft_processor = None
    best_exec_processor = None
    min_eft = float("inf")
    min_exec_time = float("inf")

    for p_id in self.sim.processors:
      eft = self.sim.calc_eft(task_id, p_id)

      if eft < min_eft:
        min_eft = eft
        best_eft_processor = p_id

      execution_time = self.sim.execution_cost[task_id].get(p_id, 0.0)
      if execution_time < min_exec_time:
        min_exec_time = execution_time
        best_exec_processor = p_id

    if best_eft_processor is None or best_exec_processor is None:
      raise RuntimeError(f"Unable to select processors for task {task_id}.")

    best_eft_exec_time = self.sim.execution_cost[task_id].get(best_eft_processor, 0.0)
    if best_eft_exec_time <= min_exec_time:
      return task_id, best_eft_processor

    weight_abstract = self.weight_abstract(task_id, min_eft, best_exec_processor)
    cross_threshold = self.cross_threshold(task_id, weight_abstract)
    if cross_threshold <= random.uniform(0.1, 0.3):
      return task_id, best_eft_processor

    return task_id, best_exec_processor

  def weight_abstract(self, task_id: str, min_eft: float, pk: str) -> float:
    eft_j = min_eft
    eft_k = self.sim.calc_eft(task_id, pk)

    if eft_j == 0 or eft_k == 0:
      return 0.0

    return abs((eft_j - eft_k) / (eft_j / eft_k))

  def cross_threshold(self, ni: str, weight_abstract: float) -> float:
    if weight_abstract <= 0:
      return float("inf")

    return self.weight(ni) / weight_abstract

  def rank_proposed(self, ni: str) -> float:
    if ni in self._rank_proposed:
      return self._rank_proposed[ni]

    max_succ_weight = 0
    for succ_id in self.sim.workflow.tasks_children[ni]:
      comm_cost = self.sim.calc_communication_cost(ni, succ_id) 
      max_succ_weight = max(max_succ_weight, comm_cost + self.rank_proposed(succ_id))

    self._rank_proposed[ni] = self.weight(ni) + max_succ_weight
    return self._rank_proposed[ni]
  
  def weight(self, ni: str) -> float:
    if ni in self._weight_cache:
      return self._weight_cache[ni]

    highest = max(self.sim.execution_cost[ni].values())
    lowest = min(self.sim.execution_cost[ni].values())

    if highest == 0 or lowest == 0:
      return 0.0

    self._weight_cache[ni] = abs((highest - lowest) / (highest / lowest))
    return self._weight_cache[ni]