import os
import pathlib
from pathlib import Path
from typing import Dict, Set
from wfcommons import wfinstances
from wfcommons.common import Task

from research.simulator import Workflow

class Config:
  def __init__(self, ignore_memory: bool = False, reference_speed: float = 10.0):
    self.ignore_memory = ignore_memory
    self.reference_speed = reference_speed

def file_size_in_mb(size: int, schema_version: str, wms: str) -> float:
  if (schema_version == "1.4" and wms != "Makeflow") or wms == "Pegasus":
    return size / 1e6
  else:
    return size / 1e3

def from_wfcommons(file_path: Path, config: Config) -> Workflow:
  d = os.path.dirname(os.path.realpath(__file__))
  path = pathlib.Path(d, '..', 'dag-instances', 'wfcommons')
  instance = wfinstances.Instance(input_instance=path.joinpath("blast-chameleon-small-005.json"))
  wf_workflow = instance.workflow
  machines = instance.machines

  # machine.cpu.speed in WfCommons format actually refers to CPU speed in MHz,
  # but it seems everyone use it as Mflop/s too...
  # here we convert it to Gflop/s
  machine_speed = {
    m.name: m.cpu_speed / 1000.0
    for m in machines.values() if m.cpu_speed is not None
  }

  workflow = Workflow()
  data_items: Dict[str, int] = {}
  task_ids: Dict[str, int] = {}

  for task_id in wf_workflow:
    task: Task = wf_workflow.tasks[task_id]
    cores = int(task.cores or 1)

    if config.ignore_memory:
      memory = 0
    else:
      """Convert bytes to megabytes, rounding up to the nearest integer."""
      memory = int((task.memory or 0) / 1e3 + 0.9999)

    # flops
    flops = task.runtime * float(cores)
    if task.machine is not None and task.machine in machine_speed:
        flops *= machine_speed[task.machine]
    else:
        flops *= config.reference_speed

    task_id = workflow.add_task(task.name, flops, memory, cores, cores, CoresDependency.Linear)
    task_ids[task.name] = task_id

    for f in task.files:
      if f.link == "output":
        data_items[f.name] = workflow.add_task_output(task_id, f.name, file_size_in_mb(f.size, schema_version, wms_name))

  for task in wf_workflow.tasks():
    task_id = task_ids[task.name]
    predecessors: Set[int] = set()

    for f in task.files:
      if f.link == "input":
        if f.name in data_items:
          data_item_id = data_items[f.name]
          producer = workflow.get_data_item(data_item_id).producer
          if producer is not None:
            predecessors.add(producer)
          workflow.add_data_dependency(data_item_id, task_id)
        else:
          data_item_id = workflow.add_data_item(f.name, file_size_in_mb(f.size, schema_version, wms_name))
          data_items[f.name] = data_item_id
          workflow.add_data_dependency(data_item_id, task_id)

    for parent in task.parents:
      parent_id = task_ids[parent]
      if parent_id not in predecessors:
        data_item_id = workflow.add_task_output(parent_id, f"{parent} -> {task.name}", 0.0)
        workflow.add_data_dependency(data_item_id, task_id)
        predecessors.add(parent_id)

  return workflow
