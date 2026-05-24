from dataclasses import dataclass, field
from typing import Any

@dataclass(slots=True)
class SimulationMetrics:
  history: list[dict[str, Any]]
  workflow: Any
  CP: list[str]
  execution_cost: dict[str, dict[str, float]]
  CPmin: list[tuple[str, float]] = field(init=False, default_factory=list)

  def __post_init__(self):
    for task_id in self.CP:
      min_cost = min(self.execution_cost[task_id].values()) if self.execution_cost[task_id] else 0
      self.CPmin.append((task_id, min_cost))

  def makespan(self) -> float:
    return max((entry["end"] for entry in self.history), default=0)

  def slr(self) -> float:
    cpmin_cost = sum(cost for _, cost in self.CPmin)
    makespan = self.makespan()
    return makespan / cpmin_cost if cpmin_cost else 0

  def throughput(self) -> float:
    task_count = len(self.workflow.tasks)
    makespan = self.makespan()
    return task_count / (makespan or 1)

  def log(self, logger: Any) -> None:
    makespan = self.makespan()
    slr = self.slr()
    throughput = self.throughput()

    logger.info("Scheduler finished.")
    logger.info(f"Makespan: {makespan}")
    logger.info(f"SLR: {slr}")
    logger.info(f"Throughput: {throughput:.8f} tasks/s")