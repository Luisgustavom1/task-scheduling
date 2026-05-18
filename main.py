import argparse
import logging
from os import path
import os
import pathlib
import sys

from simulator import Simulator
from wfcommons import wfinstances
from schedulers.fifo import FIFOScheduler
from schedulers.heft import HEFT

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
  choices=["FIFO", "HEFT"],
  help="Select scheduling algorithm.",
)
args = parser.parse_args()

logging.basicConfig(
    level=getattr(logging, args.log_level.upper()),
    handlers=[logging.StreamHandler(sys.stdout)],
)

d = os.path.dirname(os.path.realpath(__file__))
path = pathlib.Path(d, 'dag-instances', 'wfcommons')

workflow: wfinstances.Instance = wfinstances.Instance(
  input_instance=path.joinpath("bwa-chameleon-small-001.json"), 
  logger=logging.getLogger(__name__)
)

simulator = Simulator(workflow, bandwidth=1e6, logger=logging.getLogger(__name__))

# Instantiate scheduler based on user selection
scheduler_map = {
  "FIFO": FIFOScheduler,
  "HEFT": HEFT,
}
scheduler_class = scheduler_map[args.scheduler]
scheduler = scheduler_class(simulator)

simulator.start(scheduler)