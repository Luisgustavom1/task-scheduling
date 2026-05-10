from wfcommons import common, wfinstances
from common import Task, Resource

class Simulator:
  def __init__(self, instance: wfinstances.Instance, logging: bool = True):
    self.instance: wfinstances.Instance = instance
    self.workflow: common.Workflow = instance.workflow
    self.logging = logging

    self.start_task: common.Task
    self.exit_task: common.Task
    self.resources: dict[str, Resource] = {}
    self.completed_tasks: list[Task] = []
    self.time = 0
    self.average_transfer_rate = -1

    self.normalizeStartTasks()
    self.normalizeExitTasks()
    self.calcAverageTransferRate()
    self.populateResources()
    self.calcExectTime()

  def calcExectTime(self):
    for task_id in self.workflow.nodes:
      wf_task: common.Task = self.workflow.tasks[task_id]
      resourceExecTime: dict[str, float] = {}
      machines = wf_task.machines or []

      if machines:
        for machine in machines:
          resourceExecTime[machine.name] = wf_task.runtime

        reference_resource = self.resources[machines[0].name]
        for resource in self.resources.values():
          if resource.name not in resourceExecTime:
            resourceExecTime[resource.name] = self.estimateExecTime(
              reference_resource,
              resource,
              wf_task.runtime,
            )
      else:
        for resource in self.resources.values():
          resourceExecTime[resource.name] = wf_task.runtime
  
  def populateResources(self):
    for resource_id in self.instance.machines:
      resource = self.instance.machines[resource_id]
      self.resources[resource_id] = resource

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
      is_start_task = len(self.workflow.tasks_parents[task]) == 0
      if is_start_task:
        start_tasks.append(task)

    if len(start_tasks) > 1:
      entry_point = common.Task(
        task_id="entry_point",
        name="entry_point",
        runtime=0,
        cores=0,
        input_files=[],
        output_files=[],
        machines=[]
      )

      self.start_task = entry_point

      self.workflow.add_task(entry_point)
      self.workflow.tasks_children[entry_point.name] = set()
      for task in start_tasks:
        self.workflow.add_edge(entry_point.name, task)
        self.workflow.tasks_children[entry_point.name].add(task)
        self.workflow.tasks_parents[task].add(entry_point.name)

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
      artificial_exit_task = common.Task(
        task_id="artificial_exit_task",
        name="artificial_exit_task",
        runtime=0,
        cores=0,
        input_files=[],
        output_files=[],
        machines=[]
      )

      self.exit_task = artificial_exit_task

      self.workflow.add_task(artificial_exit_task)
      self.workflow.tasks_parents[artificial_exit_task.name] = set()
      for task in exit_tasks:
        self.workflow.add_edge(task, artificial_exit_task.name)
        self.workflow.tasks_parents[artificial_exit_task.name].add(task)
        self.workflow.tasks_children[task].add(artificial_exit_task.name)

  def start(self, scheduler):
    self.logger("Starting scheduler...")
    scheduler.start(self.instance, list(self.resources.values()))
    self.logger("Scheduler finished.")

  # def calcUpwardRank(self, task: Task):
  #   if task.rank_u is not None:
  #     return task.rank_u
    
  #   successors = []
  #   for parent_id in task.parents:
  #     parent = self.tasks[parent_id]
  #     succRankU = self.calcUpwardRank(parent) or 0.0
  #     avgCommunicationCost = self.calcAvgCommunicationCost(task, parent)
  #     successors.append(avgCommunicationCost + succRankU)

  #   task_avg_exec_time = task.avg_exec_time or 0.0
  #   task.rank_u = task_avg_exec_time if len(successors) == 0 else task_avg_exec_time + np.amax(successors)

  #   return task.rank_u
  
  # def calcDownwardRank(self, task: Task):
  #   if task.rank_d is not None:
  #     return task.rank_d

  #   predecessors = []
  #   for child_id in task.children:
  #     child = self.tasks[child_id]
  #     predRankD = self.calcDownwardRank(child)
  #     avgCommunicationCost = self.calcAvgCommunicationCost(task, child)
  #     predecessors.append(predRankD + (child.avg_exec_time or 0.0) + avgCommunicationCost)

  #   task.rank_d = 0 if len(predecessors) == 0 else np.amax(predecessors)
  #   return task.rank_d

  # def calcAvgCommunicationCost(self, taski: Task, taskj: Task):
  #   out_transfer = sum([file.size for file in taski.output_files])
  #   in_transfer = sum([file.size for file in taskj.input_files])
  #   avgCommunicationCost = (out_transfer + in_transfer) / self.average_transfer_rate

  #   return avgCommunicationCost

  def estimateExecTime(self, original_resource: Resource, new_resource: Resource, original_time):
    original_capacity = original_resource.cpu_cores * original_resource.cpu_speed
    new_capacity = (new_resource.cpu_cores * new_resource.cpu_speed) or 1
    
    estimated_time = original_time * (original_capacity / new_capacity)
    
    return estimated_time

  def logger(self, message):
    if self.logging:
      print(message)