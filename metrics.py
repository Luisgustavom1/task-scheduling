from dataclasses import dataclass
from typing import Any
from schedulers.scheduler import Instance

@dataclass(slots=True)
class SimulationMetrics:
  _history: list[dict[str, Any]]
  _instance: Instance
  # critical path
  _CP: list[str]
  _execution_cost: dict[str, dict[str, float]]
  # Precompute minimum execution cost for critical path tasks
  _CPmin: list[tuple[str, float]] | None = None
  _makespan: int = 0
  _load_balance: float | None = None
  _communication_cost: float | None = None
  _total_wait_time: float | None = None

  def makespan(self) -> float:
    if self._makespan == 0.0:
      self._makespan = max((entry["end"] for entry in self._history), default=0)
    return self._makespan

  def CPmin(self) -> list[tuple[str, float]]:
    if self._CPmin:
      return self._CPmin
    
    self._CPmin = []
    for task_id in self._CP:
      min_cost = min(self._execution_cost[task_id].values()) if self._execution_cost[task_id] else 0
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
      pid = entry["processor_id"]
      duration = entry["end"] - entry["start"]
      if pid not in proc_workload:
        proc_workload[pid] = 0.0
      proc_workload[pid] += duration

    total_workload = sum(proc_workload.values())

    if total_workload == 0 or len(self._instance.machines) == 0:
      self._load_balance = 0.0
      return self._load_balance
    
    avg_workload = total_workload / len(self._instance.machines)
    self._load_balance = self.makespan() / avg_workload

    return self._load_balance

  def communicationCost(self) -> float:
    if self._communication_cost is not None:
      return self._communication_cost
    self._communication_cost = sum(entry.get("communication_cost", 0.0) for entry in self._history)
    return self._communication_cost

  def totalWaitTime(self) -> float:
    if self._total_wait_time is not None:
      return self._total_wait_time
    total = 0.0
    for entry in self._history:
      start = float(entry.get("start", 0.0))
      data_ready = float(entry.get("data_ready_time", 0.0))
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