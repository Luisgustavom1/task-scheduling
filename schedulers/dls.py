from typing import Dict
from schedulers.scheduler import Scheduler, Task
from simulator import Simulator

class DLS(Scheduler):
  def __init__(self, simulator: Simulator):
    self.name = "DLS"
    self.sim = simulator
    self._rank: Dict[str, float] = {}

  def schedule(self) -> tuple[str, str]:
    if not self._rank:
      for task_id in self.sim.workflow.tasks:
        self.rank_tasks(task_id)

    unescheduled_tasks = list(self.sim.ready_tasks)

    if not unescheduled_tasks:
      raise RuntimeError("No unscheduled tasks remaining.")

    unescheduled_tasks.sort(key=lambda tid: (
      -self._rank[tid],                       # 1. Highest rank first (Descending)
      self.sim.workflow.tasks[tid].priority,         # 2. Lowest priority first (Ascending)
    ))

    task_id = unescheduled_tasks.pop(0)

    self.sim.ready_tasks.remove(task_id)

    max_dl = 0.0
    best_processor = None

    for p_id in self.sim.processors:
      dl = self.DL(task_id, p_id)
      if abs(dl) > max_dl:
        max_dl = dl
        best_processor = p_id

    if best_processor is None:
      raise RuntimeError(f"Unable to select processors for task {task_id}.")
    
    return task_id, best_processor

  def rank_tasks(self, ni: str) -> float:
    if ni in self._rank:
      return self._rank[ni]

    max_communication_cost = 0.0
    for pred_id in self.sim.workflow.tasks_parents[ni]:
      comm_cost = self.sim.calc_communication_cost(pred_id, ni)
      if comm_cost > max_communication_cost:
        max_communication_cost = comm_cost

    self._rank[ni] = self.SL(ni) + max_communication_cost

    return self._rank[ni]
  
  # The level of node N, is defined as the largest sum of execution times along any
  # directed path from N, to an endnode of the graph, over all
  # endnodes of the graph
  def SL(self, ni: str) -> float:
    if ni not in self.sim.workflow.tasks_children:
      self._rank[ni] = 0.0
      return 0.0

    max_succ_weight = 0.0
    for succ_id in self.sim.workflow.tasks_children[ni]:
      comm_cost = self.sim.calc_communication_cost(ni, succ_id)
      succ_rank = self.SL(succ_id)
      weight = comm_cost + succ_rank
      if weight > max_succ_weight:
        max_succ_weight = weight

    exec_time_avg = sum(self.sim.execution_cost[ni].values()) / len(self.sim.execution_cost[ni])
    self._rank[ni] = exec_time_avg + max_succ_weight
    return self._rank[ni]

  # maximization term represents the earliest time that node N ,
  # can start execution on processor PI
  # defined by -> DL(ni, pj) = SL(Ni) - max[DA(ni, pj)]
  def DL(self, ni: str, pj: str) -> float:
    sl = self.SL(ni)
    da = self.DA(ni, pj)

    return sl - da

  # Earliest time that all data required by node N , is available
  # at processor P3 at state C ( t ) . This quantity, calculated within
  # the topology-dependent section of the scheduler, represents the
  # earliest time at which all data transfers to node N , from its
  # immediate predecessors can be guaranteed to be completed
  # with all communication resources reserved in advance.
  def DA(self, ni: str, pj: str) -> float:
    earliest_data_available = 0.0
    for pred_id in self.sim.workflow.tasks_parents[ni]:
      pred_processor = self.sim.task_allocation.get(pred_id)
      if pred_processor is None:
        raise RuntimeError(f"Predecessor task {pred_id} has not been allocated to any processor.")

      comm_cost = self.sim.calc_communication_cost(pred_id, ni, pj)
      exec_time = self.sim.execution_cost[pred_id].get(pred_processor, 0.0)
      earliest_data_available = max(earliest_data_available, comm_cost + exec_time)

    return earliest_data_available