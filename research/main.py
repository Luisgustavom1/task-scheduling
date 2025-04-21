import pathlib
import os
from wfcommons import wfinstances, common
from schedulers import FIFOScheduler, HEFTScheduler
from simulator import Task, Resource, Simulator

d = os.path.dirname(os.path.realpath(__file__))
path = pathlib.Path(d, '..', 'dag-instances', 'wfcommons')
instance = wfinstances.Instance(input_instance=path.joinpath("blast-chameleon-large-002.json"))

simulator = Simulator(instance)
scheduler = HEFTScheduler()
simulator.start(scheduler)
print(simulator.time)

# 143146.052228 -> HEFT
# 144182.946722 -> FIFO