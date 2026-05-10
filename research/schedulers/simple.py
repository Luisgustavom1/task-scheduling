import resource
from typing import List
from scheduler import Action, ScheduleTask, Scheduler
from wfcommons import wfinstances
from common import Resource, Task

class SimpleScheduler(Scheduler):
  def start(self, dag: wfinstances.Instance, resources: List[Resource]):
    result: List[Action] = [];
    for task_id in dag.workflow.tasks:
      task: Task = dag.workflow.tasks[task_id];
      for i in range(len(resources)):
        resource = resources[i];
        task_cores = int(task.cores or 0)
        task_memory = int(task.memory or 0)

        resource.cpu_cores = resource.cpu_cores or 0
        resource.memory = resource.memory or 0

        if resource.cpu_cores < task_cores or resource.memory < task_memory:
          continue;

        cores = min(resource.cpu_cores, task_cores)
        resource.cpu_cores -= cores;
        resource.memory -= task_memory;
        result.append(
            ScheduleTask(
                task=task_id,
                resource=i,
                cores=cores,
                expected_span=None
            )
        )
        break;
    
    return result