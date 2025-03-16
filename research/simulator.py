class Task:
  def __init__(self, id, name, runtime, parents, children, priority, cores):
    self.id = id
    self.name = name
    self.runtime = runtime
    self.parents = parents
    self.children = children
    self.cores = 1 if cores is None else cores
    self.priority = priority
    self.start_time = None
    self.finish_time = None

class Resource:
  def __init__(self, name, memory, core):
    self.name = name
    self.memory = memory
    self.core = core
    self.free_cores = core
    self.tasks = []

class Simulator:
  def __init__(self, tasks, resources):
    self.tasks: list[Task] = tasks
    self.resources: list[Resource] = resources
    self.completed_tasks: list[Task] = []
    self.time = 0

    self.start_task = [task for task in tasks if len(task.parents) == 0][0] 
    self.exit_task = [task for task in tasks if len(task.children) == 0][0]

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