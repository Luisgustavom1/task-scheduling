import pathlib
import os
from wfcommons import Instance, InstanceAnalyzer

d = os.path.dirname(os.path.realpath(__file__))
INSTANCES_PATH = pathlib.Path(d, '..', 'dag-instances', 'wfcommons')
instance_files = [f for f in INSTANCES_PATH.glob('*') if INSTANCES_PATH.joinpath(f).is_file()]

analyzer = InstanceAnalyzer()

for instance_file in instance_files:
    instance = Instance(input_instance=INSTANCES_PATH.joinpath(instance_file))
    analyzer.append_instance(instance)

workflow_tasks = ["split_", "blastall_", "cat_"]

instances_summary = analyzer.build_summary(workflow_tasks, include_raw_data=True)

analyzer.generate_all_fit_plots(outfile_prefix='fits/')