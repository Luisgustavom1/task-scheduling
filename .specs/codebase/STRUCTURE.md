# Project Structure & File Organization

**Root:** `/Users/luisao/ufu/task-scheduling/research/`

## Directory Layout

```
research/
│
├── main.py              ─ Entry point (CLI runner, workflow loading)
├── common.py            ─ Type aliases (Id = Union[str, int])
├── workflow.py          ─ Workflow domain model (container for tasks, data items)
├── task.py              ─ Task domain model (state machine)
├── data_item.py         ─ DataItem domain model (file/data tracking)
├── resources.py         ─ Resource domain model (compute nodes)
├── scheduler.py         ─ Scheduler base class/interface (may be external)
│
├── simulator.py         ─ Simulator orchestrator (initialization + execution)
│
├── parser/
│   └── wfcommons.py     ─ WFCommons JSON parser (from_wfcommons, Config)
│
└── schedulers/
    └── simple.py        ─ SimpleScheduler implementation (greedy allocation)
```

## File Descriptions

### Domain Models (Core Logic)

**task.py**
- Purpose: Task representation and state machine
- Key Classes:
  - TaskState (enum): PENDING, READY, SCHEDULED, RUNNABLE, RUNNING, DONE
  - Task (dataclass): name, flops, memory, min_cores, max_cores, state, inputs, outputs
- Lines: ~40
- Dependencies: enum, dataclasses
- Tests: Unit tests for state transitions (planned)

**workflow.py**
- Purpose: Workflow container and task graph management
- Key Classes:
  - Workflow (dataclass): tasks, data_items, ready_tasks, completed_task_count, inputs, outputs
- Key Methods:
  - add_task(task) → task_id
  - add_task_output(producer_id, name, size) → data_item_id
  - add_data_dependency(data_item_id, consumer_id)
- Lines: ~60
- Dependencies: dataclasses, task.py, data_item.py
- Tests: Tests for dependency management (planned)

**data_item.py**
- Purpose: Data (file) tracking between tasks
- Key Classes:
  - DataItemState (enum): PENDING, READY
  - DataItem (dataclass): name, size, state, producer, consumers
- Lines: ~20
- Dependencies: enum, dataclasses
- Tests: Tests for state transitions (planned)

**resources.py**
- Purpose: Compute node representation
- Key Classes:
  - Resource (dataclass): id, name, speed, cores, cores_available, memory, memory_available
- Lines: ~10
- Dependencies: dataclasses, common.py
- Tests: Tests for allocation logic (planned)

**common.py**
- Purpose: Shared type definitions
- Contents: Id type alias
- Lines: ~5
- Dependencies: typing
- Note: Minimal; consider expanding if more shared types emerge

---

### Entry Point & Execution

**main.py**
- Purpose: CLI interface and workflow execution orchestration
- Entry Flow:
  1. Parse command-line arguments (--silence flag)
  2. Load workflow from WFCommons JSON: from_wfcommons()
  3. Create scheduler: SimpleScheduler()
  4. Create simulator: Simulator(workflow)
  5. Run simulator: simulator.start(scheduler)
- Current Hardcoded: Workflow file = "bwa-chameleon-small-001.json"
- Lines: ~15
- Dependencies: argparse, logging, parser.wfcommons, simulator, schedulers.simple
- Tests: Integration tests (end-to-end workflow execution)

---

### Parser Layer

**parser/wfcommons.py**
- Purpose: Convert WFCommons JSON files to Workflow objects
- Key Classes:
  - Config (dataclass): ignore_memory, reference_speed
- Key Functions:
  - from_wfcommons(file_path, config) → Workflow
  - convert_bytes_to_mb(size) → int
- Process:
  1. Load JSON via wfcommons.wfinstances.Instance
  2. Extract machines and tasks
  3. Convert byte sizes to MB
  4. Estimate exec times across resources (using reference_speed)
  5. Build Workflow with tasks and dependencies
- Lines: ~100+
- Dependencies: wfcommons, math, os, pathlib, dataclasses, workflow.py, task.py
- Input: WFCommons JSON file path (relative to dag-instances/wfcommons/)
- Output: Fully populated Workflow object
- Tests: Tests for JSON parsing, size conversion, execution time estimation (planned)

---

### Simulator Layer

**simulator.py**
- Purpose: Orchestrate workflow execution and task scheduling
- Key Classes:
  - Simulator: Main orchestrator
- Key Methods:
  - `__init__(instance, logging)` — Initialize simulator
    - Tasks: normalizeStartTasks, normalizeExitTasks, calcAverageTransferRate, populateResources, populateTasks
  - `start(scheduler)` — **INCOMPLETE** (should run event loop)
  - `populateResources()` — Build Resource objects from WFCommons
  - `populateTasks()` — Build Task objects with exec time estimates
  - `estimateExecTime(ref_resource, target, runtime)` — Estimate task exec time on heterogeneous resources
  - `calcAverageTransferRate()` — Compute network transfer rate 🔴 RETURNS NONE
  - `calcDownwardRank()` — Calculate task priorities 🔴 RETURNS NONE
- Lines: ~200+
- Dependencies: numpy, workflow.py, task.py, resources.py, scheduler interface
- State Maintained: tasks dict, resources dict, completed_tasks list, time, start_task, exit_task
- Tests: Tests for initialization, resource population, task estimation (planned)

**Key Issue:** Execution loop not implemented; start() returns immediately after scheduler call.

---

### Scheduler Layer

**schedulers/simple.py**
- Purpose: Implement a simple greedy task scheduling algorithm
- Key Classes:
  - SimpleScheduler (inherits from Scheduler)
- Key Methods:
  - `start(workflow, resources) → List[Action]`
    - Iterates over ready tasks
    - Allocates each to first available resource
    - Returns ScheduleTask actions
- Strategy: Greedy, first-fit
- Limitations: No prioritization, no topology awareness
- Lines: ~30
- Dependencies: resources.py, scheduler interface, workflow.py
- Tests: Tests for allocation logic, edge cases (planned)

---

### Data Flow: File → Execution

```
dag-instances/wfcommons/bwa-chameleon-small-001.json
                    ↓
            main.py (entry point)
                    ↓
        parser/wfcommons.from_wfcommons()
                    ↓
            Workflow object (tasks, data_items, resources)
                    ↓
        Simulator.__init__() (normalization, population)
                    ↓
    simulator.start(scheduler)
                    ↓
        scheduler.start() → ScheduleTask actions
                    ↓
    [INCOMPLETE: Event loop should process actions]
                    ↓
            Metrics: makespan, task times, utilization
```

---

## External Dependencies (Outside research/)

**Parent Directory (`../`):**
- `dag-instances/wfcommons/` — Real workflow DAG files in WFCommons format
- `ve/` — Virtual environment with dependencies (numpy, pandas, wfcommons, etc.)

**Workspace Context (Reference Only):**
- `genetic-algorithms/` — Separate research project (NOT part of current scope)
- `wfcommons/` — Tooling and utility code (NOT part of current scope)

---

## File Size & Complexity

| File | Lines | Complexity | Status |
|---|---|---|---|
| task.py | ~40 | Low | ✓ Complete |
| data_item.py | ~20 | Low | ✓ Complete |
| workflow.py | ~60 | Medium | ✓ Complete |
| resources.py | ~10 | Low | ✓ Complete |
| common.py | ~5 | Trivial | ✓ Complete |
| main.py | ~15 | Low | ✓ Complete (hardcoded DAG path) |
| parser/wfcommons.py | ~100+ | High | ✓ Complete |
| simulator.py | ~200+ | High | ⚠️ Partial (execution loop missing) |
| schedulers/simple.py | ~30 | Medium | ⚠️ Partial (no prioritization) |

---

## Code Ownership & Review Notes

- **Domain models** (task.py, workflow.py, etc.): Well-designed, follow DDD principles
- **Parser** (wfcommons.py): Mature, handles edge cases
- **Simulator** (simulator.py): Partial implementation; needs execution loop and error handling
- **Scheduler** (simple.py): Functional but naive; ready for enhancement

---

## Planned: Future File Structure

**For v1.1+:**
```
research/
├── metrics/
│   ├── __init__.py
│   ├── collector.py      ─ Makespan, utilization calculation
│   └── reporter.py       ─ Output formatting
├── events/
│   ├── __init__.py
│   └── event_queue.py    ─ Priority queue for discrete events
├── config/
│   ├── defaults.py
│   └── load_config.py
└── tests/
    ├── conftest.py       ─ Fixtures, sample data
    ├── test_parser.py
    ├── test_simulator.py
    └── integration/
```

---

## How to Run

```bash
cd /Users/luisao/ufu/task-scheduling
source ve/bin/activate
cd research
python main.py              # Run with default DAG
python main.py --silence    # Run without logging
```

**Current Issue:** Execution incomplete; simulator.start() does not run workflows end-to-end.
