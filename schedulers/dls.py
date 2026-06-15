from typing import Dict
from schedulers.scheduler import Scheduler
from simulator import Simulator
import statistics

class DLS(Scheduler):
  def __init__(self, simulator: Simulator):
    self.name = "DLS"
    self.sim = simulator
    self._rank: Dict[str, float] = {}
    self._SL_cache: Dict[str, float] = {}

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

    best_dl = -float('inf')
    best_processor = None
    task_id = None
    
    for tid in unescheduled_tasks:
      for pj in self.sim.processors:
        dl = self.DL(tid, pj)
        if dl > best_dl:
          best_dl = dl
          best_processor = pj
          task_id = tid

    if task_id is None or best_processor is None:
      raise RuntimeError("Unable to select a task and processor for scheduling.")
    
    self.sim.ready_tasks.remove(task_id)

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
    if ni in self._SL_cache:
      return self._SL_cache[ni]

    exec_time_avg = self.E(ni)
    # leaf node
    if ni not in self.sim.workflow.tasks_children or not self.sim.workflow.tasks_children[ni]:
      self._SL_cache[ni] = exec_time_avg
      return self._SL_cache[ni]

    max_succ_weight = 0.0
    for succ_id in self.sim.workflow.tasks_children[ni]:
      succ_rank = self.SL(succ_id)
      if succ_rank > max_succ_weight:
        max_succ_weight = succ_rank

    self._SL_cache[ni] = exec_time_avg + max_succ_weight
    return self._SL_cache[ni]

  def E(self, ni: str) -> float:
    execution_times = list(self.sim.execution_cost[ni].values())
    median = statistics.median(execution_times)

    if median == float('inf'):
      finite_times = [et for et in execution_times if et != float('inf')]
      if not finite_times:
        raise RuntimeError(f"Task {ni} cannot be executed on ANY processor.")
      median = max(finite_times)
      
    return median

  def delta(self, ni: str, pj: str) -> float:
    return self.E(ni) - self.get_execution_time(ni, pj)
  # maximization term represents the earliest time that node N ,
  # can start execution on processor PI
  # defined by -> DL(ni, pj) = SL(Ni) - max[DA(ni, pj)] + delta(ni, pj)
  def DL(self, ni: str, pj: str) -> float:
    sl = self.SL(ni)

    tf = self.sim.processors[pj].available_at
    da = self.DA(ni, pj)
    delta = self.delta(ni, pj)

    return sl - max(da, tf) + delta

  def DC(self, ni: str, pj: str) -> float:
    descendant = self.D(ni)
    if descendant is None:
      return 0.0

    e = self.E(descendant)
    exec_time = self.get_execution_time(descendant, pj)
    f = self.F(ni, descendant, pj)

    return e - min(f, exec_time)
  
  def F(self, ni: str, d_ni: str, pj: str) -> float:
    comm_cost = self.sim.calc_communication_cost(ni, d_ni)
    min_exec_time = float('inf')

    for pk in self.sim.processors:
      if pk == pj:
        continue

      exec_time = self.get_execution_time(d_ni, pk)
      if exec_time < min_exec_time:
        min_exec_time = exec_time
    
    if min_exec_time == float('inf'):
      self.sim.logger.warning(f"Descendant {d_ni} cannot execute on any processor other than {pj}.")
      return float('inf')  # The time to finish elsewhere is strictly infinite

    return comm_cost + min_exec_time
  
  # we consider the descendant to which Ni, passes the most data,
  def D(self, ni: str) -> str | None:
    max_comm_cost = -1.0
    descendant_id = None
    for succ_id in self.sim.workflow.tasks_children[ni]:
      comm_cost = self.sim.calc_communication_cost(ni, succ_id)
      if comm_cost > max_comm_cost:
        max_comm_cost = comm_cost
        descendant_id = succ_id

    return descendant_id

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

      pred_finish_time = self.sim.completed_tasks.get(pred_id, 0.0)
      comm_cost = self.sim.calc_communication_cost(pred_id, ni, pj)
      earliest_data_available = max(earliest_data_available, comm_cost + pred_finish_time)

    return earliest_data_available
  
  def get_execution_time(self, ni: str, pj: str) -> float:
    return self.sim.execution_cost[ni].get(pj, float('inf'))