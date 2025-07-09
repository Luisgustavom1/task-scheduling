from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple


@dataclass
class RunStats:
  scheduling_times: List[float] = field(default_factory=list)
  expected_makespan: Optional[float] = None
  total_network_traffic: float = 0.0
  transfer_starts: Dict[int, float] = field(default_factory=dict)  # data_item -> start_time
  task_starts: Dict[int, Tuple[int, int, float]] = field(default_factory=dict)  # task -> (cores, memory, start_time)
  used_resources: set[int] = field(default_factory=set)  # Set of resources used 
  task_resource: Dict[int, int] = field(default_factory=dict)
  resource_first_used: Dict[int, float] = field(default_factory=dict)  # resource -> first used time
  resource_last_used: Dict[int, float] = field(default_factory=dict)  # resource -> last used time

  def add_scheduling_time(self, time_seconds: float) -> None:
    self.scheduling_times.append(time_seconds)
  
  def set_expected_makespan(self, makespan: float) -> None:
    self.expected_makespan = makespan

  def set_transfer_start(self, data_item: int, size: float, time: float):
    self.total_network_traffic += size;
    self.transfer_starts[data_item] = time;

  def set_task_start(self, task: int, resource: int, cores: int, memory: int, time: float):
    self.current_cores += cores;
    self.max_used_cores = self.max_used_cores.max(self.current_cores);
    self.current_memory += memory;
    self.max_used_memory = self.max_used_memory.max(self.current_memory);
    self.task_starts[task] = (cores, memory, time);
    self.used_resources.add(resource);
    self.task_resource[task] = resource;
    self.resource_first_used.setdefault(resource, time);

  def set_task_finish(self, task: int, time: float):
    (cores, memory, start_time) = self.task_starts.pop(task);
    self.current_cores -= cores;
    self.current_memory -= memory;
    self.total_task_time += time - start_time;
    self.cpu_utilization += (time - start_time) * cores;
    self.memory_utilization += (time - start_time) * memory;
    self.resource_last_used[self.task_resource[task]] = time;
