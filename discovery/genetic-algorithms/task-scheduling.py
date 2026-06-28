import copy
import random

class MSE:
  def __init__(self, dic, numeroTarefas, numeroProcessadores):
    self.dic                 = dic
    self.numeroTarefas       = numeroTarefas
    self.numeroProcessadores = numeroProcessadores

  def create_chromosome(self):
    chromosome = {"allocation": [], "scheduling": []}
    tasks_list = [copy.deepcopy(self.dic[t]) for t in range(self.numeroTarefas)]

    i = 0
    processors_list = range(self.numeroProcessadores)

    while len(chromosome["scheduling"]) < self.numeroTarefas:
      if i == 0:
        task_index = 0
        i += 1
      else:
        if not tasks_list:
          break
        task_index = random.randrange(len(tasks_list))

      task = tasks_list[task_index]
      task_number = task["task"]
      predecessors = task["predecessors"]

      if (
        task_number not in chromosome["scheduling"]
        and self._predecessors_allocated(chromosome["scheduling"], predecessors)
      ):
        chromosome["scheduling"].append(task_number)
        chromosome["allocation"].append(random.choice(processors_list))
        tasks_list.pop(task_index)

    self._simulate(chromosome)

    return chromosome
  
  def _simulate(self, chromosome):
    finish_time = {}
    proc_free = [0] * self.numeroProcessadores
    proc_workload = [0] * self.numeroProcessadores

    total_comm_cost = 0
    total_wait_time = 0
    total_finish_sum = 0

    for index, task in enumerate(chromosome["scheduling"]):
      processor = chromosome["allocation"][index]
      predecessors = self.dic[task]["predecessors"]

      ready_time = 0
      for i, pred in enumerate(predecessors):
        finish_pred = finish_time.get(pred, 0)
        index_pred = chromosome["scheduling"].index(pred)
        proc_pred = chromosome["allocation"][index_pred]

        comm_cost = 0
        if proc_pred != processor:
          comm_cost = int(self.dic[task]["comm_costs"][i])
          total_comm_cost += comm_cost

        ready_time = max(ready_time, finish_pred + comm_cost)
      
      start_time = max(ready_time, proc_free[processor])

      total_wait_time += start_time - ready_time

      exec_time = int(self.dic[task]["exec_times"][processor])
      ft = start_time + exec_time
      finish_time[task] = ft

      proc_free[processor] = ft
      proc_workload[processor] += exec_time
      total_finish_sum += ft

    makespan = max(finish_time.values()) if finish_time else 0

    total_workload = sum(proc_workload)
    if total_workload > 0:
      avg_workload = total_workload / self.numeroProcessadores
      load_balance = makespan / avg_workload
    else:
      load_balance = 0.0

    total_capacity = makespan * self.numeroProcessadores
    utilization = total_workload / total_capacity if total_capacity > 0 else 0.0

    avg_workload_std = total_workload / self.numeroProcessadores
    workload_std = (
      (sum((w - avg_workload_std) ** 2 for w in proc_workload) / self.numeroProcessadores) ** 0.5
    )

    chromosome["makespan"]          = makespan
    chromosome["flowtime"]          = total_finish_sum
    chromosome["waitingTime"]       = total_wait_time
    chromosome["communicationCost"] = total_comm_cost
    chromosome["loadBalance"]       = load_balance
    chromosome["utilization"]       = utilization
    chromosome["workloadStd"]       = workload_std
  
  def _predecessors_allocated(self, scheduling, predecessors):
    for predecessor in predecessors:
      if predecessor not in scheduling:
        return False
    return True
  
  def create_initial_population(self, population_size):
    population = []
    for _ in range(population_size):
      population.append(self.create_chromosome())
    return population
  
def parse_stg(file_path):
  with open(file_path, 'r') as file:
    lines = file.readlines()

  header = lines[0].strip().split()
  if len(header) < 2:
    header = lines[1].strip().split()
    start_idx = 2
  else:
    start_idx = 1

  num_processors = int(header[1])

  dic = {}
  for line in lines[start_idx:]:
    parts = line.strip().split()
    if not parts:
      continue

    task_id = int(parts[0])
    exec_times = [int(x) for x in parts[1:num_processors + 1]]
    num_predecessors = int(parts[num_processors + 1])

    predecessors = []
    comm_costs = []
    current_idx = num_processors + 2

    for _ in range(num_predecessors):
      if current_idx + 1 >= len(parts):
        break

      predecessors.append(int(parts[current_idx]))
      comm_costs.append(int(parts[current_idx + 1]))
      current_idx += 2 

    dic[task_id] = {
      "task": task_id,
      "predecessors": predecessors,
      "comm_costs": comm_costs,
      "exec_times": exec_times,
    }

  return dic, len(dic), num_processors

stg = parse_stg("/Users/luisao/ufu/task-scheduling/discovery/genetic-algorithms/sample.stg")

mse = MSE(stg[0], stg[1], stg[2])

print("Creating chromosome:")
print(mse.create_chromosome())