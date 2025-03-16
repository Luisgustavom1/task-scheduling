import pathlib
import os
from wfcommons import wfinstances, common
from schedulers import FIFOScheduler, HEFTScheduler
from simulator import Task, Resource, Simulator

d = os.path.dirname(os.path.realpath(__file__))
path = pathlib.Path(d, '..', 'dag-instances', 'wfcommons')
instance = wfinstances.Instance(input_instance=path.joinpath("blast-chameleon-large-002.json"))
workflow = instance.workflow

tasks: list[Task] = []

for task_id in workflow:
  task: common.Task = workflow.tasks[task_id]
  # TODO: find a better way to get IDs
  children = [int(child.split('_ID')[1])-1 for child in workflow.tasks_children[task_id]]
  parents = [int(parent.split('_ID')[1])-1 for parent in workflow.tasks_parents[task_id]]

  ID = int(task_id.split('_ID')[1])-1

  tasks.append(
    Task(
      ID,
      task.name, 
      task.runtime,
      parents, 
      children,
      ID if task.priority is None else task.priority, 
      task.cores,
    )
  )

resources: list[Resource] = []

for resource_id in instance.machines:
  resource = instance.machines[resource_id]
  resources.append(
    Resource(
      resource_id,
      resource.memory,
      resource.cpu_cores
    )
  )

simulator = Simulator(tasks, resources)
scheduler = FIFOScheduler()
simulator.start(scheduler)
print(simulator.time)

# 143146.052228
# 144182.946722