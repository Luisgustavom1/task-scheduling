from dataclasses import dataclass, field
from typing import List, Set

from task import Task, TaskState
from data_item import DataItem, DataItemState

@dataclass
class Workflow:
  tasks: List[Task] = field(default_factory=list)
  data_items: List[DataItem] = field(default_factory=list)
  ready_tasks: Set[int] = field(default_factory=set)
  completed_task_count: int = 0
  inputs: Set[int] = field(default_factory=set)
  outputs: Set[int] = field(default_factory=set)
  logging: bool = True

  def add_task(self, task: Task):
    task_id = len(self.tasks)
    self.tasks.append(task)
    self.ready_tasks.add(task_id)
    return task_id

  def add_task_output(self, producer: int, name: str, size: float) -> int:
    data_item = DataItem(
      name=name,
      size=size,
      state=DataItemState.PENDING,
      producer=producer
    )
    data_item_id = len(self.data_items)
    self.data_items.append(data_item)
    self.tasks[producer].outputs.append(data_item_id)
    self.outputs.add(data_item_id)
    return data_item_id

  def add_data_dependency(self, data_item_id: int, consumer_id: int) -> None:
    data_item = self.data_items[data_item_id]
    data_item.consumers.append(consumer_id)

    consumer = self.tasks[consumer_id]
    consumer.inputs.append(data_item_id)
    
    self.outputs.discard(data_item_id)
    
    if (data_item.state == DataItemState.PENDING and consumer.state == TaskState.READY):
      consumer.state = TaskState.PENDING
      self.ready_tasks.discard(consumer_id)
    elif data_item.state == DataItemState.READY:
      consumer.ready_inputs += 1

  def add_data_item(self, name: str, size: float) -> int:
    data_item = DataItem(
      name=name,
      size=size,
      state=DataItemState.READY,
      producer=None
    )
    data_item_id = len(self.data_items)
    self.data_items.append(data_item)
    self.inputs.add(data_item_id)
    self.outputs.add(data_item_id)
    return data_item_id

  def get_data_items(self) -> List[DataItem]:
    return self.data_items

  def get_data_item(self, id: int) -> DataItem:
    return self.data_items[id]

  def get_tasks(self) -> List[Task]:
    return self.tasks
  
  def logger(self, message):
    if self.logging:
      print(message)