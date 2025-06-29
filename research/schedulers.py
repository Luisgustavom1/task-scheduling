from simulator import Simulator

class FIFOScheduler:
  def schedule(self, s):
    return sorted(s.tasks)
  
class HEFTScheduler:
  def __init__(self, s: Simulator):
    self.s = s

  def schedule(self):
    self.s.calcUpwardRank(self.s.exit_task)

    # check if has some task with rank_u None
    for task_id in self.s.tasks:
      task = self.s.tasks[task_id]
      if task.rank_u is None:
        raise ValueError(f"Task {task.name} has rank_u None")
    
    nodes = sorted(list(self.s.tasks.values()), key=lambda x: x.rank_u)

    while len(nodes) > 0:
      ni = nodes.pop()

      for resource in self.s.resources.values():
        if resource.free_cores >= ni.cores:
          self.s.logger(f"Task {ni.name} scheduled on resource {resource.name} at time {self.s.time}")

          ni.start_time = self.s.time
          ni.end_time = self.s.time + ni.avgExecTime

          resource.free_cores -= ni.cores
          resource.tasks.append(ni)

          self.s.completed_tasks.append(ni)
          self.s.time = max(self.s.time, ni.end_time)
          break

    return 