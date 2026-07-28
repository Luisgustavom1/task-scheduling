import argparse
import logging
import pathlib
import sys
import os
import random

from wfcommons.common import Machine

from charts import plot_machine_scaling
from metrics import SimulationMetrics
from schedulers.dls import DLS
from schedulers.peft import PEFT
from simulator import Simulator
from wfcommons import wfinstances
from schedulers.heft import HEFT
from schedulers.ipeft import IPEFT
from schedulers.iheft import IHEFT

parser = argparse.ArgumentParser(description="Run the task scheduler.")
parser.add_argument("--silence", action="store_true", help="Disable logging for the scheduler.", default=False)
parser.add_argument(
  "--log-level",
  default="DEBUG",
  choices=["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"],
  help="Set the logging level.",
)
parser.add_argument(
  "--scheduler",
  choices=["HEFT", "PEFT", "IPEFT", "IHEFT", "DLS"],
  help="Select scheduling algorithm.",
)
parser.add_argument(
  "--compare",
  action="store_true",
  default=False,
  help="Run all algorithms and plot comparison charts for each metric.",
)
parser.add_argument(
  "--dag-path",
  default="dag-instances/wfcommons/bwa-chameleon-small-001.json",
  help="Path to a DAG JSON file or a directory containing DAG JSON files. Relative paths are resolved from the repository root.",
)

args = parser.parse_args()

logging.basicConfig(
    level=getattr(logging, args.log_level.upper()),
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

repo_root = pathlib.Path(__file__).resolve().parent
dag_path = pathlib.Path(args.dag_path)
if not dag_path.is_absolute():
  dag_path = repo_root / dag_path

if not dag_path.exists():
  parser.error(f"DAG file not found: {dag_path}")

# Instantiate scheduler based on user selection
scheduler_map = {
  "HEFT": HEFT,
  "PEFT": PEFT,
  "IPEFT": IPEFT,
  "IHEFT": IHEFT,
  "DLS": DLS,
}

def load_dag_paths(path: pathlib.Path) -> list[pathlib.Path]:
  if path.is_file():
    return [path]

  if path.is_dir():
    dag_paths = sorted(
      candidate
      for candidate in path.iterdir()
      if candidate.is_file() and candidate.suffix.lower() == ".json"
    )

    if not dag_paths:
      parser.error(f"No DAG JSON files found in directory: {path}")

    return dag_paths

  parser.error(f"DAG path must be a file or directory: {path}")

instMap = {}

def load_workflow(path: pathlib.Path, num_machines: None | int) -> wfinstances.Instance:
  if (path, num_machines) in instMap:
    return instMap[(path, num_machines)]

  inst = wfinstances.Instance(
    input_instance=path,
    logger=logger,
  )

  if num_machines is not None:
    machines = {}

    rng = random.Random(42)  # Fixed seed for reproducibility
    
    for i in range(num_machines):
      p = i + 1
      gamma_p = rng.uniform(0.75, 1.25)
      speed = int(gamma_p * 1000) 
      
      machines[f'machine{p}'] = Machine(
        name=f"machine{p}",
        cpu={"vendor": "Custom", "coreCount": 8, "speedInMHz": speed},
      )
    
    inst.machines = machines

  instMap[(path, num_machines)] = inst
  return inst

def run_scheduler(algorithm: str, path: pathlib.Path, num_machines: int | None = None) -> SimulationMetrics:
  workflow = load_workflow(path, num_machines)
  simulator = Simulator(workflow, bandwidth=1250, logger=logger)
  scheduler = scheduler_map[algorithm](simulator)
  simulator.start(scheduler)
  return SimulationMetrics(simulator)

dag_paths = load_dag_paths(dag_path)

if args.compare:
  algorithms = ["HEFT", "IHEFT", "PEFT", "IPEFT", "DLS"]
  machine_counts = [4, 8, 16, 32]

  for dag_file in dag_paths:
    logger.info(f"\n========================================")
    logger.info(f"=== Simulating for DAG: {dag_file.name} ===")
    logger.info(f"========================================")

    results_dir = dag_file.parent / f"{dag_file.stem}-results"

    if results_dir.exists():
      logger.info(f"======= A pasta de resultados '{results_dir.name}' já existe. Pulando simulação... ====")
      continue

    results_dir.mkdir(parents=True, exist_ok=True)
    
    inst = load_workflow(dag_file, 4)

    tasks_qtd = len(inst.workflow.tasks)
    scheduler_info = {
      'tasks_qtd': tasks_qtd,
    }

    original_cwd = os.getcwd()
    os.chdir(results_dir)
    try:
      inst.draw(extension=".png")

      with open("info.txt", "w") as f:
        for key, value in scheduler_info.items():
          f.write(f"{key}: {value}\n")

      logger.info(f"DAG layout image saved in {results_dir.name}/")
    except Exception as e:
      logger.warning(f"Could not save files {dag_file.name}: {e}")
    finally:
      os.chdir(original_cwd)
      
    metrics_by_machine_count = {count: {} for count in machine_counts}

    for count in machine_counts:
      logger.info(f"--- Simulating for {count} machines ---")
      for algorithm in algorithms:
        metrics_by_machine_count[count][algorithm] = run_scheduler(algorithm, dag_file, count)

    plot_machine_scaling(
      algorithms=algorithms, 
      metrics_by_machine_count=metrics_by_machine_count,
      output_dir=results_dir
    )
    logger.info(f"Charts saved successfully in {results_dir.name}/")

  sys.exit(0)

if args.scheduler:
  if not dag_path.is_file():
    parser.error("A flag --scheduler só pode ser usada com um único arquivo DAG específico, não com um diretório inteiro. Utilize --compare para análises de diretórios.")
    
  metrics = run_scheduler(args.scheduler, dag_path, 8)
  metrics.log(logger)
else:
  logger.error("No scheduler selected. Use --scheduler to select an algorithm or --compare to run all algorithms.")