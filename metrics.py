from dataclasses import dataclass, field
from typing import Any
from common import History
from simulator import Simulator

@dataclass(slots=True)
class SimulationMetrics:
  _sim: Simulator
  # Precompute minimum execution cost for critical path tasks
  _CPmin: list[tuple[str, float]] | None = None
  _makespan: int = 0
  _load_balance: float | None = None
  _communication_cost: float | None = None
  _total_wait_time: float | None = None
  _history: list[History] = field(default_factory=list)

  def __post_init__(self):
    self._history = [item for sublist in self._sim.history.values() for item in sublist]

  def makespan(self) -> float:
    if self._makespan == 0.0:
      self._makespan = max(self._sim.completed_tasks.values(), default=0)
    return self._makespan

  def CPmin(self) -> list[tuple[str, float]]:
    if self._CPmin:
      return self._CPmin
    
    self._CPmin = []
    for task_id in self._sim.CP:
      min_cost = min(self._sim.execution_cost[task_id].values()) if self._sim.execution_cost[task_id] else 0
      self._CPmin.append((task_id, min_cost))

    return self._CPmin

  def slr(self) -> float:
    cpmin_cost = sum(cost for _, cost in self.CPmin())
    makespan = self.makespan()
    return makespan / cpmin_cost if cpmin_cost else 0

  def loadBalance(self) -> float:
    if self._load_balance is not None:
      return self._load_balance

    proc_workload: dict[str, float] = {}

    for entry in self._history:
      pid = entry.processor_id
      duration = entry.end - entry.start
      if pid not in proc_workload:
        proc_workload[pid] = 0.0
      proc_workload[pid] += duration

    total_workload = sum(proc_workload.values())

    if total_workload == 0 or len(self._sim.instance.machines) == 0:
      self._load_balance = 0.0
      return self._load_balance
    
    avg_workload = total_workload / len(self._sim.instance.machines)
    self._load_balance = self.makespan() / avg_workload

    return self._load_balance

  def communicationCost(self) -> float:
    if self._communication_cost is not None:
      return self._communication_cost
    self._communication_cost = sum(entry.communication_cost for entry in self._history)
    return self._communication_cost

  def totalWaitTime(self) -> float:
    if self._total_wait_time is not None:
      return self._total_wait_time
    total = 0.0
    for entry in self._history:
      start = float(entry.start)
      data_ready = float(entry.data_ready_time)
      total += max(0.0, start - data_ready)
    self._total_wait_time = total
    return self._total_wait_time

  def log(self, logger: Any) -> None:
    makespan = self.makespan()
    slr = self.slr()

    logger.info("Scheduler finished.")
    logger.info(f"Makespan: {makespan}")
    logger.info(f"SLR: {slr}")
    logger.info(f"Load Balance: {self.loadBalance()}")
    logger.info(f"Communication Cost: {self.communicationCost()}")
    logger.info(f"Total Wait Time: {self.totalWaitTime()}")