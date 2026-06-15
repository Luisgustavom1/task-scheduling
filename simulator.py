from collections import deque
import logging
from typing import Dict, cast

from schedulers.scheduler import Instance, Scheduler, Task, Workflow, Processor
from common import convert_machine_speed, file_size_in_mb, History

class Simulator:
  def __init__(self, instance: Instance, bandwidth: float, logger: logging.Logger | None = None):
    self.instance: Instance = instance
    self.workflow: Workflow = instance.workflow
    self.logger = logger or logging.getLogger(__name__)
    self.bandwidth = bandwidth

    self.ready_tasks: deque[str] = deque()
    self.processors: Dict[str, Processor] = cast(Dict[str, Processor], instance.machines)
    for processor in self.processors.values():
      setattr(processor, "available_at", 0.0)

    self.completed_tasks = {} # task_id -> end_time
    self.history: Dict[str, list[History]] = {} # machine_id -> history of scheduled tasks on that machine

    self.start_task: Task = self.build_artifical_tasks("artificial_entry_point", priority=1)
    self.exit_task: Task = self.build_artifical_tasks("artificial_exit_point", priority=int(1e9))

    self.task_allocation: Dict[str, str] = {} # task_id -> machine_id
    
    self.execution_cost: Dict[str, Dict[str, float]] = {} # task_id -> machine_id -> runtime
    self.avg_execution_cost: Dict[str, float] = {} # task_id -> average runtime across all machines
    self._communication_cost: Dict[str, Dict[str, float]] = {} # task_id -> machine_id -> cost
    self.CP = [] # critical path tasks

    self.normalizeStartTasks()
    self.normalizeExitTasks()
    self.buildExecutionCost()
    self.buildCommunicationCost()
    self.buildAvgExecutionCost()
    self.calcCP()

  def build_artifical_tasks(self, id: str, priority: int = 0) -> Task:
    return Task(
      task_id=id,
      name=id,
      runtime=0,
      cores=0,
      priority=priority,
      input_files=[],
      output_files=[],
      machines=[]
    )

  def normalizeStartTasks(self):
    """
    Normalize the start tasks in the workflow.

    This method identifies tasks in the workflow that have no parents and create a artificial task to represent the entry point of workflow.

    This normalization is essential for ensuring the workflow structure is valid and can be processed correctly by the scheduler.
    """
    start_tasks = []
    for task in self.workflow.tasks:
      is_start_task = len(self.workflow.tasks_parents[task]) == 0
      if is_start_task:
        start_tasks.append(task)

    if len(start_tasks) > 1:
      entry_point = self.start_task
      self.workflow.add_task(entry_point)
      self.workflow.tasks_children[entry_point.name] = set()
      for task in start_tasks:
        self.workflow.add_edge(entry_point.name, task)
        self.workflow.tasks_children[entry_point.name].add(task)
        self.workflow.tasks_parents[task].add(entry_point.name)
    else:
      self.start_task = self.workflow.tasks[start_tasks[0]]

  def normalizeExitTasks(self):
    """
    Normalize the exit tasks in the workflow.

    This method identifies tasks in the workflow that have no children and create a artificial task to represent the endpoint of workflow.

    This normalization is essential for ensuring the workflow structure is valid and can be processed correctly by the scheduler.
    """
    exit_tasks = []
    for task in self.workflow.tasks:
      is_exit_task = len(self.workflow.tasks_children[task]) == 0
      if is_exit_task:
        exit_tasks.append(task)

    if len(exit_tasks) > 1:
      artificial_exit_task = self.exit_task
      self.workflow.add_task(artificial_exit_task)
      self.workflow.tasks_parents[artificial_exit_task.name] = set()
      for task in exit_tasks:
        self.workflow.add_edge(task, artificial_exit_task.name)
        self.workflow.tasks_parents[artificial_exit_task.name].add(task)
        self.workflow.tasks_children[task].add(artificial_exit_task.name)
    else:
      self.exit_task = self.workflow.tasks[exit_tasks[0]]

  def buildExecutionCost(self):
    for task_id, task in self.workflow.tasks.items():
      self.execution_cost[task_id] = {}
      for machine_id, processor in self.processors.items():
        runtime = self.calculate_task_runtime(task, processor)
        self.execution_cost[task_id][machine_id] = runtime

  def buildCommunicationCost(self):
    for task_id_i, task_i in self.workflow.tasks.items():
      self._communication_cost[task_id_i] = {}
      for task_id_j in self.workflow.tasks_children.get(task_id_i, []):
        task_j: Task = self.workflow.tasks[task_id_j]

        shared_files = set(task_i.output_files) & set(task_j.input_files)
        total_size = sum(
          file_size_in_mb(f.size, self.instance.runtime_system["name"])
          for f in shared_files
        )
        # maybe this calculation of communication cost is wrong
        self._communication_cost[task_id_i][task_id_j] = total_size / self.bandwidth
  
  def buildAvgExecutionCost(self):
    for task_id in self.workflow.tasks:
      costs = self.execution_cost[task_id].values()
      self.avg_execution_cost[task_id] = sum(costs) / len(costs) if costs else 0

  def calcCP(self):
    tasks = [self.start_task.task_id]

    while len(tasks) > 0:
      task_id = tasks.pop(0)
      self.CP.append(task_id)

      children = self.workflow.tasks_children.get(task_id, [])
      if len(children) == 0 and task_id != self.exit_task.task_id:
        raise ValueError(f"Task {task_id} has no children but is not the exit task. Workflow may be malformed.")
      
      if len(children) == 0:
        self.logger.debug(f"Task {task_id} is an exit task.")
        continue

      max_cost = -1
      max_cost_child = None
      for child_id in children:
        for runtime in self.execution_cost[child_id].values():
          cost = runtime + self._communication_cost.get(task_id, {}).get(child_id, 0)
          if cost > max_cost:
            max_cost = cost
            max_cost_child = child_id

      if not max_cost_child:
        raise ValueError(f"Could not find child with max cost for task {task_id}")

      tasks.append(max_cost_child)

    self.logger.info(f"Critical path: {' -> '.join(self.CP)}")

  def start(self, scheduler: Scheduler, visualizer=None):
    self.logger.info(f"Starting scheduler...")
    
    self.ready_tasks.append(self.start_task.task_id)

    if visualizer is not None and hasattr(visualizer, "attach"):
      visualizer.attach(self)

    while len(self.completed_tasks) < len(self.workflow.tasks):
      if not self.ready_tasks:
        self.logger.warning("No ready tasks, but workflow is not complete. Possible deadlock or missing dependencies.")
        break

      action = scheduler.schedule()
      self.logger.debug(f"Scheduler selected action: {action}")

      task_id, machine_id = action

      start_time, communication_cost, data_ready_time = self.calc_est(task_id, machine_id)

      task: Task | None = self.workflow.tasks.get(task_id)
      if task is None:
        raise ValueError(f"Task {task_id} not found in workflow.") 

      processor_to_run = self.processors[machine_id]
      
      duration = self.calculate_task_runtime(task, processor_to_run)
      end_time = start_time + duration


      processor_to_run.available_at = max(processor_to_run.available_at, end_time)
      self.completed_tasks[task_id] = end_time
      self.task_allocation[task_id] = machine_id

      history = History(
        task_id=task_id,
        processor_id=machine_id,
        start=start_time,
        end=end_time,
        communication_cost=communication_cost,
        data_ready_time=data_ready_time,
      )
      self.add_history(history)
      self.logger.debug(f"history computed {history}")

      if visualizer is not None and hasattr(visualizer, "on_task_scheduled"):
        visualizer.on_task_scheduled(
          task=task,
          processor_id=machine_id,
          start_time=start_time,
          end_time=end_time,
          ready_time=start_time,
        )

      self.logger.debug(f"task {task_id} escalonada para máquina {machine_id} ({start_time}s -> {end_time}s)")

      for child_id in self.workflow.tasks_children.get(task_id, []):
        parents: Dict[str, set[str]] = self.workflow.tasks_parents
        
        # we only add the child task to the ready queue if all its parent tasks have been completed
        if all(task in self.completed_tasks for task in parents.get(child_id, [])):
          if child_id not in self.ready_tasks:
            self.ready_tasks.append(child_id)

    if visualizer is not None and hasattr(visualizer, "finalize"):
      visualizer.finalize()

    return

  def add_history(self, history: History):
    if history.processor_id not in self.history:
      self.history[history.processor_id] = []
    self.history[history.processor_id].append(history)
    self.history[history.processor_id].sort(key=lambda x: x.start)

  def calculate_task_runtime(self, task: Task, processor: Processor) -> float:
    if task.task_id.startswith("artificial_"):
      return 0.0
    
    if task.machines is None or len(task.machines) == 0 or len(task.machines) > 1:
      raise ValueError(f"Task {task.task_id} has no specific machine or multiple machines on execution specs, using default runtime.")

    machine_runner = task.machines[0]
    machine_runner_speed = convert_machine_speed(machine_runner.cpu_speed)
    task_cores = task.cores or 1

    flops = task.runtime * machine_runner_speed * task_cores

    processor_speed = convert_machine_speed(processor.cpu_speed)

    return flops / processor_speed / task_cores

  def calc_communication_cost(self, task_id_i: str, task_id_j: str, possible_processor_j: str | None = None) -> float:
    if possible_processor_j is not None and self.task_allocation.get(task_id_i) == possible_processor_j:
      return 0

    return self._communication_cost.get(task_id_i, {}).get(task_id_j, 0.0)

  def avg_communication_cost(self, ti: str, pi: str, tk: str, pk: str) -> float:
    if pi == pk:
      return 0.0

    return self._communication_cost.get(ti, {}).get(tk, 0.0)

  # return est time and the communication cost to run task ti on processor pj
  # est -> the earliest time that task ti can start on processor pj considering the finish time of its parent tasks and the communication cost
  def calc_est(self, task_id: str, processor_id: str) -> tuple[float, float, float]:
    execution_time = self.execution_cost[task_id].get(processor_id, 0.0)
    communication_cost = 0.0
    data_ready_time = 0
    for p_id_parent in self.workflow.tasks_parents[task_id]:
      parent_finish = self.completed_tasks[p_id_parent]

      if parent_finish is None:
        raise ValueError(f"Parent task {p_id_parent} of task {task_id} has not been completed yet.")

      comm_cost = self.calc_communication_cost(p_id_parent, task_id, processor_id)
      communication_cost += comm_cost
      data_ready_time = max(data_ready_time, parent_finish + comm_cost)

    schedules = self.history.get(processor_id)
    if not schedules:
      return data_ready_time, communication_cost, data_ready_time

    first_task_start = schedules[0].start
    if data_ready_time + execution_time <= first_task_start:
      return data_ready_time, communication_cost, data_ready_time

    # schedules
    # (0, 3)
    # (3, 5)
    # ... gap 3 time (5, 10) -> 10 - 5 = 5
    # (10, 12)
    for i in range(len(schedules) - 1):
      gap_start = max(data_ready_time, schedules[i].end) # max(data_ready_time, end of prev task)
      gap_end = schedules[i + 1].start # start of next task

      if gap_end - gap_start >= execution_time:
        return gap_start, communication_cost, data_ready_time

    process_available_at = schedules[-1].end
    return max(process_available_at, data_ready_time), communication_cost, data_ready_time