from typing import List
from resources import Resource
from scheduler import Action, ScheduleTask, Scheduler
from workflow import Workflow

class SimpleScheduler(Scheduler):
  def start(self, workflow: Workflow, resources: List[Resource]):
    result: List[Action] = [];
    ready_tasks = workflow.ready_tasks.copy()
    for task_id in ready_tasks:
      task = workflow.get_task(task_id);
      for i in range(len(resources)):
        resource = resources[i];
        if resource.cores_available < task.min_cores or resource.memory_available < task.memory:
          continue;

        cores = min(resource.cores_available, task.max_cores)
        resource.cores_available -= cores;
        resource.memory_available -= task.memory;
        result.append(
            ScheduleTask(
                task=task_id,
                resource=i,
                cores=cores,
                expected_span=None
            )
        )
        break;
