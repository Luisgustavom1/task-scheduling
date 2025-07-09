import argparse

from parser.wfcommons import from_wfcommons, Config
from runner import Runner
from schedulers.simple import SimpleScheduler

parser = argparse.ArgumentParser(description="Run the task scheduler.")
parser.add_argument("--silence", action="store_true", help="Disable logging for the scheduler.", default=False)
args = parser.parse_args()

workflow = from_wfcommons("bwa-chameleon-small-001.json", Config(ignore_memory=True, reference_speed=10.0))
total_tasks = workflow.get_tasks();

scheduler = SimpleScheduler()
runner = Runner(
    node_id=123,
    wf=workflow,
    scheduler=scheduler,
    resources=[],
)
runner.start()