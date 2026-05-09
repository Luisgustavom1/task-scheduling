import argparse
import logging
from os import path
import os
import pathlib
import sys

from simulator import Simulator
from wfcommons import wfinstances
from schedulers.simple import SimpleScheduler

logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stdout)])

parser = argparse.ArgumentParser(description="Run the task scheduler.")
parser.add_argument("--silence", action="store_true", help="Disable logging for the scheduler.", default=False)
args = parser.parse_args()

d = os.path.dirname(os.path.realpath(__file__))
path = pathlib.Path(d, '..', 'dag-instances', 'wfcommons')
workflow: wfinstances.Instance = wfinstances.Instance(input_instance=path.joinpath("bwa-chameleon-small-001.json"))
total_tasks = len(workflow.workflow.tasks)

logging.info(f"Total tasks: {total_tasks}")

scheduler = SimpleScheduler()
simulator = Simulator(workflow)

simulator.start(scheduler)