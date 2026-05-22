import argparse
import logging
import pathlib
import sys

from schedulers.peft import PEFT
from simulator import Simulator
from wfcommons import wfinstances
from schedulers.fifo import FIFOScheduler
from schedulers.heft import HEFT
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
  default="FIFO",
  choices=["FIFO", "HEFT", "PEFT"],
  help="Select scheduling algorithm.",
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

repo_root = pathlib.Path(__file__).resolve().parent
dag_path = pathlib.Path(args.dag_path)
if not dag_path.is_absolute():
  dag_path = repo_root / dag_path

if not dag_path.exists():
  parser.error(f"DAG file not found: {dag_path}")

workflow: wfinstances.Instance = wfinstances.Instance(
  input_instance=dag_path,
  logger=logging.getLogger(__name__)
)

simulator = Simulator(workflow, bandwidth=1e6, logger=logging.getLogger(__name__))

# Instantiate scheduler based on user selection
scheduler_map = {
  "FIFO": FIFOScheduler,
  "HEFT": HEFT,
  "PEFT": PEFT,
}
scheduler_class = scheduler_map[args.scheduler]
scheduler = scheduler_class(simulator)

visualizer = None
if args.visualize:
  visualizer = SchedulerVisualizer(
    title=f"Task Scheduling - {args.scheduler}",
    animate=True,
    frame_delay=0.03,
  )

simulator.start(scheduler, visualizer=visualizer)