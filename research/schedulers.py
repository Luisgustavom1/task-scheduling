from simulator import Task

class FIFOScheduler:
  def schedule(self, tasks: list[Task]):
    return sorted(tasks, key=lambda x: x.id)