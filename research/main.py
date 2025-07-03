import pathlib
import os
import argparse

from wfcommons import wfinstances
# from schedulers import FIFOScheduler, HEFTScheduler
# from simulator import Simulator
from parser.wfcommons import from_wfcommons, Config

parser = argparse.ArgumentParser(description="Run the task scheduler.")
parser.add_argument("--silence", action="store_true", help="Disable logging for the scheduler.", default=False)
args = parser.parse_args()

workflow = from_wfcommons("bwa-chameleon-small-001.json", Config(ignore_memory=True, reference_speed=10.0))

# simulator = Simulator(instance, not args.silence) 
# scheduler = HEFTScheduler(simulator)
# simulator.start(scheduler)
# print(simulator.time)

# 143146.052228 -> HEFT
# 144182.946722 -> FIFO