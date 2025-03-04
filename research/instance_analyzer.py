import pathlib
from wfcommons import Instance, InstanceAnalyzer

INSTANCES_PATH = pathlib.Path('path')
instance_files = [f for f in INSTANCES_PATH.glob('*') if INSTANCES_PATH.joinpath(f).is_file()]

analyzer = InstanceAnalyzer()

for instance_file in instance_files:
    instance = Instance(input_instance=INSTANCES_PATH.joinpath(instance_file))
    analyzer.append_instance(instance)

# list of workflow task name prefixes to be analyzed in each instance
workflow_tasks = ["split_", "blastall_", "cat_"]

# building the instance summary
instances_summary = analyzer.build_summary(workflow_tasks, include_raw_data=True)

# generating all fit plots (runtime, and input and output files)
analyzer.generate_all_fit_plots(outfile_prefix='fits/')