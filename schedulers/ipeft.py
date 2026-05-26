from typing import Dict
from schedulers.scheduler import Scheduler, Task
from simulator import Simulator

class IPEFT(Scheduler):
  def __init__(self, simulator: Simulator):
    self.name = "PEFT"
    self.sim = simulator
    self.aest = {} # average earliest start time
    self.alst = {} # average latest start time
    self.rank_pct: Dict[str, float] = {}
    self.cnct: Dict[tuple[str, str], float] = {}

  def schedule(self) -> tuple[str, str, float]:
    if not self.rank_pct:
      for task_id in self.sim.workflow.tasks:
        self.calc_rank_pct(task_id)

    # tasks with all parents completed and not yet scheduled
    unescheduled_tasks = [
      self.sim.workflow.tasks[tid] for tid in self.sim.workflow.tasks 
      if tid not in self.sim.completed_tasks and 
      all(p in self.sim.completed_tasks for p in self.sim.workflow.tasks_parents[tid])
    ]

    # select task with highest upward rank
    selected_task = max(unescheduled_tasks, key=lambda t: self.rank_pct[t.task_id])
    task_id = selected_task.task_id

    best_processor = list(self.sim.processors.keys())[0]
    min_optimistic_eft = float('inf')

    for pj in self.sim.processors:
      optimistic_eft = self.calc_eft_cnct(task_id, pj)

      if optimistic_eft < min_optimistic_eft:
        min_optimistic_eft = optimistic_eft
        best_processor = pj

    return task_id, best_processor, min_optimistic_eft
  
  def isCriticalNode(self, ni: str) -> bool:
    return self.calc_aest(ni) == self.calc_alst(ni)
  
  def calc_cnct(self, vi: str, pk: str) -> float:
    key = (vi, pk)
    if key in self.cnct:
      return self.cnct[key]

    successors = list(self.sim.workflow.tasks_children.get(vi, []))
    if not successors:
      self.cnct[key] = 0.0
      return 0.0

    critical_successors = [vj for vj in successors if self.isCriticalNode(vj)]
    if critical_successors:
      successors = critical_successors

    max_cnct = 0.0
    for vj in successors:
      comm_cost = self.sim.communication_cost.get(vi, {}).get(vj, 0.0)
      min_cost = min(
        self.calc_cnct(vj, pm) + self.sim.execution_cost[vj].get(pm, 0.0) + comm_cost
        for pm in self.sim.processors
      )
      max_cnct = max(max_cnct, min_cost)

    self.cnct[key] = max_cnct
    return max_cnct
  
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

  def calc_eft_cnct(self, vi: str, pj: str) -> float:
    if self.isCriticalNode(vi):
      return self.calc_eft(vi, pj)
    
    return self.calc_eft(vi, pj) + self.calc_cnct(vi, pj)

  def calc_aft(self, ni: str) -> float:
    aft = self.sim.completed_tasks[ni]
    if aft is None:
      raise ValueError(f"task {ni} has not been completed yet.")
    return aft

  # average earliest start time
  def calc_aest(self, ni: str) -> float:
    if ni in self.aest:
      return self.aest[ni]

    # if start task, aest is 0
    if len(self.sim.workflow.tasks_parents[ni]) == 0:
      return 0

    # -> entry === 0
    # -> 01 e 02 = 0 + comm_cost(entry) + avg_exec_cost(entry) === 0 + 0 + 0 === 0
    # -> 03 = maximo entre (0 + comm_cost(01) + avg_exec_cost(01)) e (0 + comm_cost(02) + avg_exec_cost(02))
    # -> exit = aest(03) + comm_cost(03) + avg_exec_cost(03)

    self.aest[ni] = max(
      self.calc_aest(nm) + self.sim.avg_execution_cost[ni] + self.sim.calc_communication_cost(nm, ni)
      for nm in self.sim.workflow.tasks_parents[ni]
    )

    return self.aest[ni]
  
  # average latest start time of task
  def calc_alst(self, ni: str) -> float:
    if ni in self.alst:
      return self.alst[ni]

    # if exit task, alst is 0
    if len(self.sim.workflow.tasks_children[ni]) == 0:
      return 0
    
    # -> entry =>
    #   min (ALST(01) - comm_cost(entry, 01)) e (ALST(02) - comm_cost(entry, 02)) - avg_exec_cost(entry) =>
    #   min (- comm_cost(03, exit) - avg_exec_cost(03) - comm_cost(01, 03) - avg_exec_cost(01) - comm_cost(entry, 01)) e (- comm_cost(03, exit) - avg_exec_cost(03) - comm_cost(02, 03) - avg_exec_cost(02) - comm_cost(entry, 02)) - 0 =>
    # -> 01 e 02 => 
    #   01. (ALST(03) - comm_cost(01, 03)) - avg_exec_cost(01) => - comm_cost(03, exit) - avg_exec_cost(03) - comm_cost(01, 03) - avg_exec_cost(01)
    #   02. (ALST(03) - comm_cost(02, 03)) - avg_exec_cost(02) => - comm_cost(03, exit) - avg_exec_cost(03) - comm_cost(02, 03) - avg_exec_cost(02)
    # -> 03 => 
    #   (ALST(exit) - comm_cost(03, exit)) - avg_exec_cost(03) => 
    #   0 - comm_cost(03, exit) - avg_exec_cost(03)
    # -> exit = 0 - 0 === 0
    
    self.alst[ni] = min(
      self.calc_alst(nm) - self.sim.calc_communication_cost(ni, nm)
      for nm in self.sim.workflow.tasks_children[ni]
    ) - self.sim.avg_execution_cost[ni]

    return self.alst[ni]

  # rank based on pessimistic cost table
  def calc_rank_pct(self, vi: str) -> float:
    if vi in self.rank_pct:
      return self.rank_pct[vi]

    pct_sum = sum(self.calc_pct(vi, pk) for pk in self.sim.processors)

    self.rank_pct[vi] = (pct_sum / len(self.sim.processors) if self.sim.processors else 0) + self.sim.avg_execution_cost[vi]

    return self.rank_pct[vi]

  # pessimistic cost table
  def calc_pct(self, vi: str, pk: str) -> float:
    pct = 0
    for vj in self.sim.workflow.tasks_children.get(vi, []):
      tmp = max(
        self.calc_pct(vj, pm) + self.sim.execution_cost[vj].get(pm, 0) + (0 if pm == pk else self.sim.calc_communication_cost(vi, vj, pk))
        for pm in self.sim.processors
      )
      pct = max(pct, tmp)
    return pct