import numpy as np
from simulator import Simulator, Task

class FIFOScheduler:
  def schedule(self, s):
    return sorted(s.tasks, key=lambda x: x.id)
  
class HEFTScheduler:
  def __init__(self):
    self.simulator = None

  def schedule(self, s: Simulator):
    self.simulator = s
    self.calcUpwardRank(s.start_task)
    return sorted(s.tasks, key=lambda x: x.id)

  def calcUpwardRank(self, task: Task):
    if task.priority is not None:
      return task.priority
    
    successors = []
    for child_id in task.children:
      # check if should be child_id - 1 ?????
      child = self.simulator.tasks[child_id]
      successorRankU = self.calcUpwardRank(child)

      out_transfer = sum([file.size for file in task.output_files])
      in_transfer = sum([file.size for file in child.input_files])
      dataTransfer = (out_transfer + in_transfer) / self.simulator.average_transfer_rate
      
      successors.append(dataTransfer + successorRankU)

    task.priority = task.runtime if len(successors) == 0 else task.runtime + np.amax(successors)

    return task.priority