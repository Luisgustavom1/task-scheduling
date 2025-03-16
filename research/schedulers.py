from simulator import Simulator

class FIFOScheduler:
  def schedule(self, s):
    return sorted(s.tasks, key=lambda x: x.id)
  
class HEFTScheduler:
  def schedule(self, s: Simulator):
    visited_tasks = {}
    max_rank = 0

    queue = []
    queue.append(s.exit_task)
    while len(queue) > 0:
      current_task = queue.pop(0)
      upward_rank = current_task.runtime + max_rank;

      if upward_rank > max_rank:
        max_rank = upward_rank

      current_task.priority = upward_rank
      visited_tasks[current_task.id] = current_task
      
      for parent in current_task.parents:
        parent_task = s.tasks[parent]
        if parent_task.id not in visited_tasks:
          queue.append(parent_task)

    print(visited_tasks)

    return sorted(visited_tasks.values(), key=lambda x: -x.priority)