import pathlib
import os
import argparse

from wfcommons import wfinstances
from schedulers import FIFOScheduler, HEFTScheduler
from simulator import Simulator

parser = argparse.ArgumentParser(description="Run the task scheduler.")
parser.add_argument("--silence", action="store_true", help="Disable logging for the scheduler.", default=False)
args = parser.parse_args()

d = os.path.dirname(os.path.realpath(__file__))
path = pathlib.Path(d, '..', 'dag-instances', 'wfcommons')
instance = wfinstances.Instance(input_instance=path.joinpath("blast-chameleon-large-002.json"))

simulator = Simulator(instance, not args.silence)
scheduler = HEFTScheduler()
simulator.start(scheduler)
print(simulator.time)

# 143146.052228 -> HEFT
# 144182.946722 -> FIFO