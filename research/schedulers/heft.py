from typing import Dict
from schedulers.scheduler import Scheduler, Processor, Task
from simulator import Simulator

class HEFT(Scheduler):
  def __init__(self, simulator: Simulator):
    self.name = "HEFT"
    self.sim = simulator
    self.up_ranks: Dict[str, float] = {}

  def schedule(self) -> tuple[str, str, float]:
    if not self.up_ranks:
      for task_id in self.sim.workflow.tasks:
        self.calc_upward_rank(self.sim.workflow.tasks[task_id])

    # tasks with all parents completed and not yet scheduled
    unescheduled_tasks = [
      self.sim.workflow.tasks[tid] for tid in self.sim.workflow.tasks 
      if tid not in self.sim.completed_tasks and 
      all(p in self.sim.completed_tasks for p in self.sim.workflow.tasks_parents[tid])
    ]

    # select task with highest upward rank
    selected_task = max(unescheduled_tasks, key=lambda t: self.up_ranks[t.task_id])
    task_id = selected_task.task_id

    best_processor = list(self.sim.processors.keys())[0]
    min_eft = float('inf')
    best_est = 0

    for p_id in self.sim.processors:
      execution_time = self.sim.execution_cost[task_id].get(p_id, 0)

      est = self.calc_est(task_id, p_id)
      eft = est + execution_time

      # schedule task to the processor that minimizes EFT
      if eft < min_eft:
        min_eft = eft
        best_processor = p_id
        best_est = est

    return task_id, best_processor, best_est

  def calc_upward_rank(self, task: Task) -> float:
    if task.task_id in self.up_ranks:
      return self.up_ranks[task.task_id]

    avg_execution_cost = self.avg_execution_cost(task)
    
    max_succ_cost = 0
    for succ_id in self.sim.workflow.tasks_children[task.task_id]:
      comm_cost = self.communication_cost(task.task_id, succ_id) 
      upward_rank = self.calc_upward_rank(self.sim.workflow.tasks[succ_id])
      max_succ_cost = max(max_succ_cost, comm_cost + upward_rank)

    self.up_ranks[task.task_id] = avg_execution_cost + max_succ_cost
    return self.up_ranks[task.task_id]

  def avg_execution_cost(self, task: Task) -> float:
    costs = self.sim.execution_cost[task.task_id].values()
    return sum(costs) / len(costs) if costs else 0

  def communication_cost(self, task_id_i: str, task_id_j: str) -> float:
    task_i: Task = self.sim.workflow.tasks[task_id_i]
    task_j: Task = self.sim.workflow.tasks[task_id_j]
    
    shared_files = set(task_i.output_files) & set(task_j.input_files)
    total_size = sum(f.size for f in shared_files)
    
    return total_size / self.sim.bandwidth
  
  def calc_est(self, task_id: str, processor_id: str) -> float:
    data_ready_time = 0
    for p_id_parent in self.sim.workflow.tasks_parents[task_id]:
      parent_finish = self.sim.completed_tasks[p_id_parent]

      if parent_finish is None:
        raise ValueError(f"Parent task {p_id_parent} of task {task_id} has not been completed yet.")

      comm_cost = 0
      # communication cost is 0 if parent and child are on the same processor
      if self.sim.task_allocation.get(p_id_parent) != processor_id:
        comm_cost = self.communication_cost(p_id_parent, task_id)
      
      data_ready_time = max(data_ready_time, parent_finish + comm_cost)

    return max(self.sim.processors[processor_id].available_at, data_ready_time)