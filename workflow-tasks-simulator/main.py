import argparse
import logging
import pathlib
import sys

from wfcommons.common import Machine, machine

from charts import plot_metric_comparison, plot_metric_trends
from metrics import SimulationMetrics
from schedulers.dls import DLS
from schedulers.peft import PEFT
from simulator import Simulator
from wfcommons import wfinstances
from schedulers.heft import HEFT
from schedulers.ipeft import IPEFT
from schedulers.iheft import IHEFT

parser = argparse.ArgumentParser(description="Run the task scheduler.")
parser.add_argument("--silence", action="store_true", help="Disable logging for the scheduler.", default=False)
parser.add_argument(
  "--log-level",
  default="DEBUG",
  choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
  help="Set the logging level.",
)
parser.add_argument(
  "--scheduler",
  choices=["HEFT", "PEFT", "IPEFT", "IHEFT", "DLS"],
  help="Select scheduling algorithm.",
)
parser.add_argument(
  "--compare",
  action="store_true",
  default=False,
  help="Run all algorithms and plot comparison charts for each metric.",
)
parser.add_argument(
  "--dag-path",
  default="dag-instances/wfcommons/bwa-chameleon-small-001.json",
  help="Path to a DAG JSON file or a directory containing DAG JSON files. Relative paths are resolved from the repository root.",
)

args = parser.parse_args()

logging.basicConfig(
    level=getattr(logging, args.log_level.upper()),
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

repo_root = pathlib.Path(__file__).resolve().parent
dag_path = pathlib.Path(args.dag_path)
if not dag_path.is_absolute():
  dag_path = repo_root / dag_path

if not dag_path.exists():
  parser.error(f"DAG file not found: {dag_path}")

# Instantiate scheduler based on user selection
scheduler_map = {
  "HEFT": HEFT,
  "PEFT": PEFT,
  "IPEFT": IPEFT,
  "IHEFT": IHEFT,
  "DLS": DLS,
}

def load_dag_paths(path: pathlib.Path) -> list[pathlib.Path]:
  if path.is_file():
    return [path]

  if path.is_dir():
    dag_paths = sorted(
      candidate
      for candidate in path.iterdir()
      if candidate.is_file() and candidate.suffix.lower() == ".json"
    )

    if not dag_paths:
      parser.error(f"No DAG JSON files found in directory: {path}")

    return dag_paths

  parser.error(f"DAG path must be a file or directory: {path}")

def load_workflow(path: pathlib.Path) -> wfinstances.Instance:
  inst = wfinstances.Instance(
    input_instance=path,
    logger=logger,
  )

  inst.machines = {
    'machine1': Machine(
      name="machine1",
      cpu={"vendor": "GenuineIntel", "coreCount": 48, "speedInMHz": 1200},
    ),
    'machine2': Machine(
      name="machine2",
      cpu={"vendor": "GenuineIntel", "coreCount": 48, "speedInMHz": 1800},
    ),
    'machine3': Machine(
      name="machine3",
      cpu={"vendor": "GenuineIntel", "coreCount": 48, "speedInMHz": 2400},
    ),
    'machine4': Machine(
      name="machine4",
      cpu={"vendor": "GenuineIntel", "coreCount": 48, "speedInMHz": 3000},
    )
  } 

  return inst

def count_tasks(path: pathlib.Path) -> int:
  workflow = load_workflow(path)
  return len(workflow.workflow.tasks)

def run_scheduler(algorithm: str, path: pathlib.Path) -> SimulationMetrics:
  workflow = load_workflow(path)
  simulator = Simulator(workflow, bandwidth=1250, logger=logger)
  scheduler = scheduler_map[algorithm](simulator)
  simulator.start(scheduler)
  return SimulationMetrics(simulator)

dag_paths = load_dag_paths(dag_path)

if args.compare:
  algorithms = list(scheduler_map.keys())

  if dag_path.is_file():
    metrics_by_algorithm: dict[str, SimulationMetrics] = {}
    for algorithm in algorithms:
      metrics_by_algorithm[algorithm] = run_scheduler(algorithm, dag_path)

    plot_metric_comparison(algorithms, metrics_by_algorithm, dag_path.name)
  else:
    runs_by_algorithm: dict[str, list[tuple[int, str, SimulationMetrics]]] = {algorithm: [] for algorithm in algorithms}

    for dag_file in dag_paths:
      task_count = count_tasks(dag_file)
      for algorithm in algorithms:
        metrics = run_scheduler(algorithm, dag_file)
        runs_by_algorithm[algorithm].append((task_count, dag_file.stem, metrics))

    plot_metric_trends(algorithms, runs_by_algorithm, dag_path.name)
  sys.exit(0)

if args.scheduler:
  if dag_path.is_file():
    metrics = run_scheduler(args.scheduler, dag_path)
    metrics.log(logger)
  else:
    for dag_file in dag_paths:
      metrics = run_scheduler(args.scheduler, dag_file)
      logger.info(f"DAG: {dag_file.name} ({count_tasks(dag_file)} tasks)")
      metrics.log(logger)
else:
  logger.error("No scheduler selected. Use --scheduler to select an algorithm or --compare to run all algorithms.")