import pathlib
import networkx as nx
import matplotlib.pyplot as plt

from wfcommons.wfbench import WorkflowBenchmark
from wfcommons import WorkflowGenerator
from wfcommons.wfchef.recipes import BlastRecipe

generator = WorkflowGenerator(BlastRecipe.from_num_tasks(105))
workflow = generator.build_workflow()
workflow.write_json(pathlib.Path(f'blast-workflow-103.json'))

benchmark = WorkflowBenchmark(recipe=generator.workflow_recipe, num_tasks=105)

path = benchmark.create_benchmark(
    pathlib.Path("./tmp/"), 
    cpu_work=100, 
    data=10, 
    percent_cpu=0.6
)

print(f"Workflow Name: {workflow.name}")
print(f"Tasks numbers: {len(workflow.tasks)}")
print(f"Edges numbers: {len(workflow.edges)}")

dag = workflow.to_nx_digraph()

# pos = nx.spring_layout(dag)
# labels = {node: data['id'] for node, data in dag.nodes(data=True)}
# nx.draw(dag, pos, labels=labels, with_labels=True, node_size=200, node_color="lightblue", font_size=10)
# plt.title("DAG do Workflow")
# plt.show()

# makespan = sum(workflow.tasks[node[0]].runtime if node[0] in workflow.tasks else 0 for node in dag.nodes(data=True))
# print(f"Makespan: {makespan} sec")

# critical_path = nx.dag_longest_path(dag, weight='runtime')
# critical_path_runtime = sum(workflow.tasks[node].runtime if node in workflow.tasks else 0 for node in critical_path)
# print(f"Critical path: {critical_path_runtime} segundos")