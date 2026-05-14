from typing import Dict, cast

from schedulers.scheduler import Scheduler, Processor, Task
from simulator import Simulator

class HEFT(Scheduler):
  def __init__(self, simulator: Simulator):
    self.name = "HEFT"
    self.sim = simulator

  def schedule(self) -> tuple[str, str, float]:
    CP = self.calc_upward_rank(self.sim.start_task)
    CPN = self.sim.start_task

    for task_id in self.sim.workflow.tasks:
      task: Task = self.sim.workflow.tasks[task_id]
      if (self.calc_downward_rank(task) + self.calc_upward_rank(task)) == CP:
        CPN = task

    queue: list[Task] = [self.sim.workflow.tasks[task_id] for task_id in self.sim.workflow.tasks if task_id not in self.sim.completed_tasks and all(pred_id in self.sim.completed_tasks for pred_id in self.sim.workflow.tasks_parents[task_id])]
    queue = sorted(queue, key=lambda task: self.calc_downward_rank(task) + self.calc_upward_rank(task))
    selected_task: Task = queue.pop(0)

    if selected_task.task_id == CPN.task_id:
      best_processor = min(self.sim.processors, key=lambda p: self.sim.processors[p].available_at)
    else:
      processors_cost = self.sim.execution_cost[selected_task.task_id]
      best_processor = min(self.sim.processors, key=lambda p: self.sim.processors[p].available_at + processors_cost.get(p, 0))

    parents: Dict[str, set[str]] = self.sim.workflow.tasks_parents[selected_task.task_id]
    est = 0
    if parents:
      est = max(self.sim.completed_tasks[p_id] + self.communication_cost(p_id, selected_task.task_id) for p_id in parents)

    return selected_task.task_id, best_processor, est
  
  # rank (ni) = avg cost of a node ni + max(avg communication cost of a edge (i,j) + rank(nj)) for nj in successors of ni
  def calc_upward_rank(self, task: Task):
    task_id = task.task_id
    return self.avg_execution_cost(task) + max(
      (self.communication_cost(task_id, succ_id) + self.calc_upward_rank(self.sim.workflow.tasks[succ_id]) for succ_id in self.sim.workflow.tasks_children[task_id]),
      default=0
    )

  # rank (ni) = max(avg communication cost of a edge (j,i) + avg cost of a node ni + rank(nj)) for nj in parents of ni
  def calc_downward_rank(self, task: Task):
    parents = self.sim.workflow.tasks_parents[task.task_id]
    if not parents:
      return 0

    return max(
      self.calc_downward_rank(self.sim.workflow.tasks[pred_id]) +
      self.avg_execution_cost(task) +
      self.communication_cost(pred_id, task.task_id)
      for pred_id in parents
    )

  def avg_execution_cost(self, task: Task) -> float:
    processors = self.sim.instance.machines
    total_runtime = sum(self.sim.execution_cost[task.task_id].get(p.name, 0) for p in processors.values())
    avg_runtime = total_runtime / len(processors)
    return avg_runtime

  def communication_cost(self, task_id_i: str, task_id_j: str) -> float:
    task_i: Task = self.sim.workflow.tasks[task_id_i]
    task_j = self.sim.workflow.tasks[task_id_j]

    files_data = set(task_i.output_files) & set(task_j.input_files)
    if len(files_data) == 0:
      return 0.0

    files_size = sum(f.size for f in files_data)

    communication_time = files_size / self.sim.bandwidth
    return communication_time