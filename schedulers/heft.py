from typing import Dict
from schedulers.scheduler import Scheduler, Task
from simulator import Simulator

class HEFT(Scheduler):
  def __init__(self, simulator: Simulator):
    self.name = "HEFT"
    self.sim = simulator
    self.up_ranks: Dict[str, float] = {}

  def schedule(self) -> tuple[str, str]:
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
    min_est = 0

    for p_id in self.sim.processors:
      execution_time = self.sim.execution_cost[task_id].get(p_id, 0)

      est, _ = self.sim.calc_est(task_id, p_id)
      eft = est + execution_time

      # schedule task to the processor that minimizes EFT
      if eft < min_eft:
        min_eft = eft
        best_processor = p_id
        min_est = est

    return task_id, best_processor

  def calc_upward_rank(self, task: Task) -> float:
    if task.task_id in self.up_ranks:
      return self.up_ranks[task.task_id]

    avg_execution_cost = self.sim.avg_execution_cost[task.task_id]
    
    max_succ_cost = 0
    for succ_id in self.sim.workflow.tasks_children[task.task_id]:
      comm_cost = self.sim.calc_communication_cost(task.task_id, succ_id) 
      upward_rank = self.calc_upward_rank(self.sim.workflow.tasks[succ_id])
      max_succ_cost = max(max_succ_cost, comm_cost + upward_rank)

    self.up_ranks[task.task_id] = avg_execution_cost + max_succ_cost
    return self.up_ranks[task.task_id]