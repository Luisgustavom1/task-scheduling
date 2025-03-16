import pathlib
import os
from wfcommons import wfinstances, common
from schedulers import FIFOScheduler
from simulator import Task, Resource, Simulator

d = os.path.dirname(os.path.realpath(__file__))
path = pathlib.Path(d, '..', 'dag-instances', 'wfcommons')
instance = wfinstances.Instance(input_instance=path.joinpath("blast-chameleon-large-002.json"))
workflow = instance.workflow

tasks: list[Task] = []

for task_id in workflow:
  task: common.Task = workflow.tasks[task_id]
  children = workflow.tasks_children[task_id]
  parents = workflow.tasks_parents[task_id]

  tasks.append(
    Task(
      task_id, 
      task.name, 
      task.runtime,
      parents, 
      children, 
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