from typing import Dict, cast

from schedulers.scheduler import Scheduler, Processor, Task
from simulator import Simulator

class HEFT(Scheduler):
  def __init__(self, simulator: Simulator):
    self.name = "HEFT"
    self.simulator = simulator

  def schedule(self) -> tuple[int, str, float]:
    ready_tasks = self.simulator.ready_tasks
    processors = self.simulator.processors
    completed_tasks = self.simulator.completed_tasks
    workflow = self.simulator.workflow

    task_id = ready_tasks.popleft()
    
    best_processor = min(processors, key=lambda p: processors[p].available_at)
    
    parents: Dict[str, set[str]] = workflow.tasks_parents[task_id]
    task_ready_time = 0
    if parents:
      task_ready_time = max(completed_tasks[p_id] for p_id in parents)
        
    return task_id, best_processor, task_ready_time
  
  # rank (ni) = avg cost of a node ni + max(avg communication cost of a edge (i,j) + rank(nj)) for nj in successors of ni
  def calc_upward_rank(self, task: Task):
    task_id = task.task_id
    return self.avg_execution_cost(task) + max(
      (self.communication_cost(task_id, succ_id) + self.calc_upward_rank(self.simulator.workflow.tasks[succ_id]) for succ_id in self.simulator.workflow.tasks_children[task_id]),
      default=0
    )

  # rank (ni) = max(avg communication cost of a edge (j,i) + avg cost of a node ni + rank(nj)) for nj in parents of ni
  def calc_downward_rank(self, task: Task):
    parents = self.simulator.workflow.tasks_parents[task.task_id]
    if not parents:
      return 0

    return max(
      self.calc_downward_rank(self.simulator.workflow.tasks[pred_id]) +
      self.avg_execution_cost(task) +
      self.communication_cost(pred_id, task.task_id)
      for pred_id in parents
    )

  def avg_execution_cost(self, task: Task) -> float:
    processors = self.simulator.instance.machines
    total_runtime = sum(self.simulator.calculate_task_runtime(task, cast(Processor, m)) for m in processors.values())
    avg_runtime = total_runtime / len(processors)
    return avg_runtime

  def communication_cost(self, task_id_i: str, task_id_j: str) -> float:
    task_i: Task = self.simulator.workflow.tasks[task_id_i]
    task_j = self.simulator.workflow.tasks[task_id_j]

    files_data = set(task_i.output_files) & set(task_j.input_files)
    if len(files_data) == 0:
      return 0.0

    files_size = sum(f.size for f in files_data)

    communication_time = files_size / self.simulator.bandwidth
    return communication_time