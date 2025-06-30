import os
import pathlib
from pathlib import Path
from typing import Dict, Set
from wfcommons import wfinstances
from wfcommons.common import Task as Wf_Task

from research.workflow import Workflow
from research.task import Task

@dataclass
class Config:
  def __init__(self, ignore_memory: bool = False, reference_speed: float = 10.0):
    self.ignore_memory = ignore_memory
    self.reference_speed = reference_speed

def convert_byte_to_mb(size: int) -> float:
  """Convert bytes to megabytes, rounding up to the nearest integer."""
  return int(size / 1e3 + 0.9999)

def from_wfcommons(file_path: Path, config: Config) -> Workflow:
  d = os.path.dirname(os.path.realpath(__file__))
  path = pathlib.Path(d, '..', 'dag-instances', 'wfcommons')
  instance = wfinstances.Instance(input_instance=path.joinpath("blast-chameleon-small-005.json"))
  wf_workflow = instance.workflow
  machines = instance.machines

  # convert speed in MHz to Gflop/s
  machine_speed = {
    m.name: m.cpu_speed / 1000.0
    for m in machines.values() if m.cpu_speed is not None
  }

  workflow = Workflow()
  data_items: Dict[str, int] = {}
  task_ids: Dict[str, int] = {}

  for task in wf_workflow.tasks.values():
    cores = int(task.cores or 1)

    if config.ignore_memory:
      memory = 0
    else:
      memory = convert_byte_to_mb(task.memory or 0)

    flops = task.runtime * float(cores)
    # TODO: check if machine is defined for the task
    if task.machine is not None and task.machine in machine_speed:
        flops *= machine_speed[task.machine]
    else:
        flops *= config.reference_speed

    task_id = workflow.add_task(
      Task(
        name=task.name,
        flops=flops,
        memory=memory,
        min_cores=cores,
        max_cores=cores,
        cores_dependency=task.cores_dependency,
      )
    )
    task_ids[task.name] = task_id

    for f in task.output_files:
      data_items[f.name] = workflow.add_task_output(task_id, f.name, file_size_in_mb(f.size))

  tasks_list = list(wf_workflow.tasks.values())
  for task_id in range(len(tasks_list)):
    task: Wf_Task = tasks_list[task_id]
    predecessors: Set[int] = set()

    for f in task.input_files:
      if f.name in data_items:
        data_item_id = data_items[f.name]
        producer: int = workflow.data_items[data_item_id].producer
        if producer is not None:
          predecessors.add(producer)
        workflow.add_data_dependency(data_item_id, task_id)
      else:
        data_item_id = workflow.add_data_item(f.name, file_size_in_mb(f.size))
        data_items[f.name] = data_item_id
        workflow.add_data_dependency(data_item_id, task_id)

    parents = wf_workflow.tasks_parents[task.task_id]
    for parent in parents:
      parent_task: Wf_Task = wf_workflow.tasks[parent]
      parent_id = task_ids[parent_task.name]
      if parent_id not in predecessors:
        data_item_id = workflow.add_task_output(parent_id, f"{parent} -> {task.name}", 0.0)
        workflow.add_data_dependency(data_item_id, task_id)
        predecessors.add(parent_id)

  return workflow
