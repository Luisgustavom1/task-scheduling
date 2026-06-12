import argparse
import logging
import pathlib
import sys

from charts import plot_metric_comparison
from metrics import SimulationMetrics
from schedulers.dls import DLS
from schedulers.peft import PEFT
from simulator import Simulator
from wfcommons import wfinstances
from schedulers.heft import HEFT
from schedulers.ipeft import IPEFT
from schedulers.iheft import IHEFT
from visualizer import SchedulerVisualizer

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
  "--visualize",
  action="store_true",
  default=False,
  help="Show a live visualization of processors and tasks while scheduling.",
)
parser.add_argument(
  "--dag-path",
  default="dag-instances/wfcommons/bwa-chameleon-small-001.json",
  help="Path to the DAG JSON file to load. Relative paths are resolved from the repository root.",
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

def load_workflow(path: pathlib.Path) -> wfinstances.Instance:
  return wfinstances.Instance(
    input_instance=path,
    logger=logger,
  )

def run_scheduler(algorithm: str, path: pathlib.Path, visualizer: SchedulerVisualizer | None = None) -> SimulationMetrics:
  workflow = load_workflow(path)
  simulator = Simulator(workflow, bandwidth=1250, logger=logger)
  scheduler = scheduler_map[algorithm](simulator)
  simulator.start(scheduler, visualizer=visualizer)
  return SimulationMetrics(simulator)

if args.compare:
  if args.visualize:
    logger.warning("--visualize is ignored when --compare is enabled.")

  algorithms = list(scheduler_map.keys())

  metrics_by_algorithm: dict[str, SimulationMetrics] = {}
  for algorithm in algorithms:
    metrics_by_algorithm[algorithm] = run_scheduler(algorithm, dag_path)

  plot_metric_comparison(algorithms, metrics_by_algorithm, dag_path.name)
  sys.exit(0)

visualizer = None
if args.visualize and args.scheduler:
  visualizer = SchedulerVisualizer(
    title=f"Task Scheduling - {args.scheduler}",
    animate=True,
    frame_delay=0.03,
  )

if args.scheduler:
  metrics = run_scheduler(args.scheduler, dag_path, visualizer)
  metrics.log(logger)
else:
  logger.error("No scheduler selected. Use --scheduler to select an algorithm or --compare to run all algorithms.")