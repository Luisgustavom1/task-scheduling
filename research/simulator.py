from wfcommons import common, wfinstances

class Task:
  def __init__(self, id, name, runtime, parents, children, priority, cores, input_files: common.File, output_files: common.File):
    self.id = id
    self.name = name
    self.runtime = runtime
    self.parents = parents
    self.children = children
    self.cores = 1 if cores is None else cores
    self.priority = priority
    self.start_time = None
    self.finish_time = None
    self.input_files: common.File = input_files
    self.output_files: common.File = output_files

class Resource:
  def __init__(self, id, name, memory, core):
    self.id = id
    self.name = name
    self.memory = memory
    self.core = core
    self.free_cores = core
    self.tasks = []

class Simulator:
  def __init__(self, instance: wfinstances.Instance):
    self.instance: wfinstances.Instance = instance
    self.workflow: common.Workflow = instance.workflow

    self.tasks: list[Task] = []
    self.resources: list[Resource] = []
    self.completed_tasks: list[Task] = []
    self.time = 0

    self.calcAverageTransferRate()
    self.populateResources()
    self.populateTasks()

    self.start_task = [task for task in self.tasks if len(task.parents) == 0][0] 
    self.exit_task = [task for task in self.tasks if len(task.children) == 0][0]

    self.average_transfer_rate = -1

  def populateTasks(self):
    for task_id in self.workflow.nodes:
      task: common.Task = self.workflow.tasks[task_id]
      # TODO: find a better way to get IDs
      children = [int(child.split('_ID')[1])-1 for child in self.workflow.tasks_children[task_id]]
      parents = [int(parent.split('_ID')[1])-1 for parent in self.workflow.tasks_parents[task_id]]

      ID = int(task_id.split('_ID')[1])-1

      self.tasks.append(
        Task(
          ID,
          task.name, 
          task.runtime,
          parents, 
          children,
          None,
          task.cores,
          task.input_files,
          task.output_files
        )
      )

  def populateResources(self):
    i = 0
    for resource_id in self.instance.machines:
      resource = self.instance.machines[resource_id]
      self.resources.append(
        Resource(
          i,
          resource_id,
          resource.memory,
          resource.cpu_cores
        )
      )
      i += 1

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

  def start(self, scheduler):
    scheduled_tasks: list[Task] = scheduler.schedule(self)

    for task in scheduled_tasks:
      for resource in self.resources:
        if resource.free_cores >= task.cores:
          print(f"Task {task.name}/{task.priority} scheduled to resource {resource.name}")
          task.start_time = self.time
          task.end_time = self.time + task.runtime

          resource.free_cores -= task.cores
          resource.tasks.append(task)

          self.completed_tasks.append(task)
          self.time = max(self.time, task.end_time)
          break