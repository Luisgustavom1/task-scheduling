# Task Scheduling Simulator

Project to simulate task scheduling on DAGs using different algorithms.

## How to run

The main simulator is in the `main.py` file.

If the virtual environment `ve` is already available, run:

```bash
./ve/bin/python main.py
```

If you prefer to use the system Python, first activate the virtual environment then execute:

```bash
source ve/bin/activate
python main.py
```

## Useful options

You can choose the scheduler with `--scheduler`:

```bash
./ve/bin/python main.py --scheduler HEFT
./ve/bin/python main.py --scheduler PEFT
```

To change the input DAG, use `--dag-path`:

```bash
./ve/bin/python main.py --dag-path dag-instances/wfcommons/blast-chameleon-large-002.json
./ve/bin/python main.py --dag-path /absolute/path/to/your-dag.json
```

Other available parameters:

- `--visualize`: shows a visualization of tasks and processors while the simulator runs.
- `--log-level`: sets the log level. Accepted values are `CRITICAL`, `ERROR`, `WARNING`, `INFO`, and `DEBUG`.
- `--silence`: disables the scheduler's logs.

## Example

```bash
./ve/bin/python main.py --scheduler HEFT --visualize --log-level INFO
```

## Next Steps

### Simulador improvements
- [ ] Consider parallelism on processors

### Algorithms
- [XX] HEFT
- [XX] IHEFT
- [X] PEFT
- [X] IPEFT
- [X] DLS

### Metrics
- [X] Makespan
- [X] SLR (scheduling length ratio)
- [X] Load balance
- [X] Communication cost
- [X] Idle time
- [X] Waiting time

### References
- Static vs. Dynamic List-SchedulingPerformance Comparison
- Análise comparativa de algoritmos de escalonamento de workflows científicos em processadores heterogêneos
- A Compile-Time Scheduling Heuristic for Interconnection-Constrained Heterogeneous Processor Architectures (DLS)
- A list scheduling algorithm for heterogeneous systems based on a critical node cost table and pessimistic cost table (IPEFT)
- Task scheduling for heterogeneous computing systems (IHEFT)
- List Scheduling Algorithm for Heterogeneous Systems by an Optimistic Cost Table (PEFT)
- Task Scheduling Algorithms for Heterogeneous Processors (HEFT)