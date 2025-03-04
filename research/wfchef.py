from wfcommons import wfinstances, common
import networkx as nx
import matplotlib.pyplot as plt

workflow = wfinstances.Instance(input_instance="../dag-instances/wfcommons/simple.json").workflow

print(f"Workflow name: {workflow.name}")
print(f"Task numbers: {len(workflow.tasks)}")
print(f"Edge numbers: {len(workflow.edges)}")

dag = workflow.to_nx_digraph()

makespan = sum(workflow.tasks[node[0]].runtime if node[0] in workflow.tasks else 0 for node in dag.nodes(data=True))
print(f"Makespan: {makespan} sec")

critical_path = nx.dag_longest_path(dag, weight='runtime')
critical_path_runtime = sum(workflow.tasks[node].runtime if node in workflow.tasks else 0 for node in critical_path)
print(f"Critical path: {critical_path_runtime} segundos")

pos = nx.spring_layout(dag)
labels = {node: data['id'] for node, data in dag.nodes(data=True)}
nx.draw(dag, pos, labels=labels, with_labels=True, node_size=200, node_color="lightblue", font_size=10)
plt.title("DAG do Workflow")
plt.show()