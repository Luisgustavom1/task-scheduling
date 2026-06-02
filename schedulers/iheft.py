import random
from typing import Dict
from schedulers.scheduler import Scheduler, Task
from simulator import Simulator

class IHEFT(Scheduler):
  def __init__(self, simulator: Simulator):
    self.name = "IHEFT"
    self.sim = simulator
    self.weights: Dict[str, float] = {}

  def schedule(self) -> tuple[str, str]:
    if not self.weights:
      for task_id in self.sim.workflow.tasks:
        self.rank_proposed(task_id)

    task_id = max(self.sim.ready_tasks, key=lambda tid: self.weights[tid])

    best_eft_processor = None
    best_exec_processor = None
    min_eft = float("inf")
    min_exec_time = float("inf")

    for p_id in self.sim.processors:
      execution_time = self.sim.execution_cost[task_id].get(p_id, 0.0)
      est, _ = self.sim.calc_est(task_id, p_id)
      eft = est + execution_time

      if eft < min_eft:
        min_eft = eft
        best_eft_processor = p_id

      if execution_time < min_exec_time:
        min_exec_time = execution_time
        best_exec_processor = p_id

    if best_eft_processor is None or best_exec_processor is None:
      raise RuntimeError(f"Unable to select processors for task {task_id}.")

    best_eft_exec_time = self.sim.execution_cost[task_id].get(best_eft_processor, 0.0)
    if best_eft_exec_time <= min_exec_time:
      return task_id, best_eft_processor

    weight_abstract = self.weight_abstract(task_id, best_eft_processor, best_exec_processor)
    cross_threshold = self.cross_threshold(task_id, weight_abstract)
    if cross_threshold <= random.random():
      return task_id, best_eft_processor

    return task_id, best_exec_processor

  def weight_abstract(self, task_id: str, pj: str, pk: str) -> float:
    eft_j = self.calc_eft(task_id, pj)
    eft_k = self.calc_eft(task_id, pk)

    if eft_j == 0 or eft_k == 0:
      return 0.0

    return abs((eft_j - eft_k) / (eft_j / eft_k))

  def cross_threshold(self, ni: str, weight_abstract: float) -> float:
    if weight_abstract <= 0:
      return float("inf")

    return self.rank_proposed(ni) / weight_abstract

  def calc_eft(self, task_id: str, processor_id: str) -> float:
    est, _ = self.sim.calc_est(task_id, processor_id)
    return est + self.sim.execution_cost[task_id].get(processor_id, 0.0)

  def rank_proposed(self, ni: str) -> float:
    if ni in self.weights:
      return self.weights[ni]

    weight = self.weight(ni)
    max_succ_weight = 0
    for succ_id in self.sim.workflow.tasks_children[ni]:
      comm_cost = self.sim.calc_communication_cost(ni, succ_id) 
      max_succ_weight = max(max_succ_weight, comm_cost + self.rank_proposed(succ_id))

    self.weights[ni] = weight + max_succ_weight
    return self.weights[ni]
  
  def weight(self, ni: str) -> float:
    highest = max(self.sim.execution_cost[ni].values())
    lowest = min(self.sim.execution_cost[ni].values())

    if highest == 0 or lowest == 0:
      return 0.0

    return abs((highest - lowest) / (highest / lowest))