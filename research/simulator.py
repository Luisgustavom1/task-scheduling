import numpy as np
from wfcommons import common, wfinstances
from typing import List, Optional, Set
from enum import Enum

class Cpu:
  speed: Optional[int]

class Machine:
  name: str
  cpu: Cpu


class File:
  name: str
  size: int
  link: str


class Task:
  name: str
  runtime: float
  cores: Optional[float] = None
  memory_in_bytes: Optional[int] = None
  memory: Optional[int] = None
  files: List[File] = []
  machine: Optional[str] = None
  parents: List[str] = []

class DataItemState(Enum):
  PENDING = "Pending"  
  READY = "Ready"

class DataItem:
  def __init__(
    self,
    name: str,
    size: float,  # MB
    producer: Optional[int] = None,
    consumers: Optional[List[int]] = None,
    state: DataItemState = DataItemState.PENDING,
  ):
    self.name = name
    self.size = size
    self.producer = producer
    self.consumers = consumers if consumers is not None else []
    self.state = state

class Workflow:
  tasks: List['Task'] = []
  data_items: List['DataItem'] = []
  ready_tasks: Set[int] = []
  completed_task_count: int = 0
  inputs: Set[int] = []
  outputs: Set[int] = []

class Simulator:
  def __init__(self, instance: wfinstances.Instance, logging: bool = True):
    self.instance: wfinstances.Instance = instance
    self.workflow: common.Workflow = instance.workflow
    self.logging = logging

    self.tasks: dict[str, Task] = {}
    self.start_task: Task = None
    self.resources: dict[str, Resource] = {}
    self.completed_tasks: list[Task] = []
    self.time = 0
    self.average_transfer_rate = -1

    self.normalizeStartTasks()
    self.normalizeExitTasks()
    self.calcAverageTransferRate()
    self.populateResources()
    self.populateTasks()

    self.start_task = [self.tasks[task_id] for task_id in self.tasks if len(self.tasks[task_id].parents) == 0][0] 
    self.exit_task = [self.tasks[task_id] for task_id in self.tasks if len(self.tasks[task_id].children) == 0][0]

  def populateTasks(self):
    for task_id in self.workflow.nodes:
      task: common.Task = self.workflow.tasks[task_id]
      resourceExecTime = {}

      for machine in task.machines:
        resourceExecTime[machine.name] = task.runtime
      
      reference_resource = self.resources[task.machines[0].name]
      for resource_id in self.resources:
        resource = self.resources[resource_id]
        if resource.name not in resourceExecTime:
          resourceExecTime[resource.name] = self.estimateExecTime(
            reference_resource, 
            resource, 
            task.runtime
          )

      self.tasks[task_id] = Task(
        task.name, 
        task.runtime, # TODO: calc avgExecTime
        resourceExecTime,
        self.workflow.tasks_parents[task_id],
        self.workflow.tasks_children[task_id],
        None,
        task.cores,
        task.input_files,
        task.output_files
      )
  
  def populateResources(self):
    for resource_id in self.instance.machines:
      resource = self.instance.machines[resource_id]
      self.resources[resource_id] = Resource(
        resource_id,
        resource.memory,
        resource.cpu_cores,
        resource.cpu_speed
      )

  def calcAverageTransferRate(self):
    all_data_transfer = 0
    for edge in self.workflow.edges:
      source = edge[0]
      target = edge[1]

      source_t: common.Task = self.workflow.tasks[source]
      target_t: common.Task = self.workflow.tasks[target]

      out_transfer = sum([file.size for file in source_t.output_files])
      in_transfer = sum([file.size for file in target_t.input_files])
      all_data_transfer += out_transfer + in_transfer

    self.average_transfer_rate = all_data_transfer / len(self.instance.machines)

  def normalizeStartTasks(self):
    """
    Normalize the start tasks in the workflow.

    This method identifies tasks in the workflow that have no parents and create a artificial task to represent the entry point of workflow.

    This normalization is essential for ensuring the workflow structure is valid and can be processed correctly by the scheduler.
    """
    start_tasks = []
    for task in self.workflow.tasks:
      if len(self.workflow.tasks_parents[task]) == 0:
        start_tasks.append(task)

    if len(start_tasks) > 1:
      artificial_start_task = common.Task(
        task_id="artificial_start_task",
        name="artificial_start_task",
        runtime=0,
        cores=1,
        input_files=[],
        output_files=[],
        machines=[]
      )

      self.workflow.add_task(artificial_start_task)
      self.workflow.tasks_children[artificial_start_task.name] = set()
      for task in start_tasks:
        self.workflow.add_edge(artificial_start_task.name, task)
        self.workflow.tasks_children[artificial_start_task.name].add(task)
        self.workflow.tasks_parents[task].add(artificial_start_task.name)

  def normalizeExitTasks(self):
    """
    Normalize the exit tasks in the workflow.

    This method identifies tasks in the workflow that have no children and create a artificial task to represent the endpoint of workflow.

    This normalization is essential for ensuring the workflow structure is valid and can be processed correctly by the scheduler.
    """
    exit_tasks = []
    for task in self.workflow.tasks:
      if len(self.workflow.tasks_children[task]) == 0:
        exit_tasks.append(task)

    if len(exit_tasks) > 1:
      artificial_exit_task = common.Task(
        task_id="artificial_exit_task",
        name="artificial_exit_task",
        runtime=0,
        cores=0,
        input_files=[],
        output_files=[],
        machines=[]
      )

      self.workflow.add_task(artificial_exit_task)
      self.workflow.tasks_parents[artificial_exit_task.name] = set()
      for task in exit_tasks:
        self.workflow.add_edge(task, artificial_exit_task.name)
        self.workflow.tasks_parents[artificial_exit_task.name].add(task)
        self.workflow.tasks_children[task].add(artificial_exit_task.name)

  def start(self, scheduler):
    self.logger("Starting scheduler...")
    scheduler.schedule()
    self.logger("Scheduler finished.")

  def calcUpwardRank(self, task: Task):
    if task.rank_u is not None:
      return task.rank_u
    
    successors = []
    for parent_id in task.parents:
      parent = self.tasks[parent_id]
      succRankU = self.calcUpwardRank(parent)
      avgCommunicationCost = self.calcAvgCommunicationCost(task, parent)
      successors.append(avgCommunicationCost + succRankU)

    task.rank_u = task.avgExecTime if len(successors) == 0 else task.avgExecTime + np.amax(successors)

    return task.rank_u
  
  def calcDownwardRank(self, task: Task):
    if task.rank_d is not None:
      return task.rank_d

    predecessors = []
    for child_id in task.children:
      child = self.tasks[child_id]
      predRankD = self.calcDownwardRank(child)
      avgCommunicationCost = self.calcAvgCommunicationCost(task, child)
      predecessors.append(predRankD + child.avgExecTime + avgCommunicationCost)

  def calcAvgCommunicationCost(self, taski: Task, taskj: Task):
    out_transfer = sum([file.size for file in taski.output_files])
    in_transfer = sum([file.size for file in taskj.input_files])
    avgCommunicationCost = (out_transfer + in_transfer) / self.average_transfer_rate

    return avgCommunicationCost

  def estimateExecTime(self, original_resource: Resource, new_resource: Resource, original_time):
    original_capacity = original_resource.core * original_resource.speed
    new_capacity = new_resource.core * new_resource.speed
    
    estimated_time = original_time * (original_capacity / new_capacity)
    
    return estimated_time

  def logger(self, message):
    if self.logging:
      print(message)