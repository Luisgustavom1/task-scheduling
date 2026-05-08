# Codebase Architecture

**Pattern:** Layered modular architecture with clear separation of concerns  
**Design Style:** Domain-Driven Design (rich domain models, explicit state machines)

## High-Level Flow

```
main.py
  ↓ (loads config + DAG file)
parser/wfcommons.py (from_wfcommons)
  ↓ (parses JSON, creates Workflow object)
workflow.py (Workflow domain model)
  ↓
simulator.py (Simulator.__init__ + start)
  ├─ Normalize tasks (start/exit tasks, transfer rates)
  ├─ Populate resources from WFCommons
  ├─ Populate tasks (map to resources, estimate exec times)
  ├─ Call scheduler.start(workflow, resources)
  └─ [INCOMPLETE: Event loop should happen here]
      ↓
schedulers/simple.py (SimpleScheduler)
  ↓ (returns list of ScheduleTask actions)
[MISSING: Main execution loop]
```

## Layer 1: Parsing (`parser/wfcommons.py`)

**Responsibility:** Convert WFCommons JSON → Workflow object

**Key Function:** `from_wfcommons(file_path, config) → Workflow`

**Process:**
1. Load WFCommons JSON using wfcommons library
2. Extract machines (resources) and tasks (workflow graph)
3. Convert byte sizes to MB
4. Estimate execution times across heterogeneous machines
5. Build Workflow object with tasks and data dependencies

**Assumptions:**
- File exists and is valid WFCommons format
- reference_speed provided (default 10.0 Gflop/s)
- Machine speeds are provided or estimated

---

## Layer 2: Domain Models

### Core Entities

**Workflow** (`workflow.py`)
- Container for tasks, data items, ready_tasks
- Tracks completion count, inputs/outputs
- Methods: add_task(), add_task_output(), add_data_dependency()
- State: mutable (modified during initialization and execution)

**Task** (`task.py`)
- State machine: PENDING → READY → SCHEDULED → RUNNABLE → RUNNING → DONE
- Fields: name, flops, memory, min_cores, max_cores, state, inputs, outputs
- No execution state (start_time, end_time, assigned_resource) — MISSING

**DataItem** (`data_item.py`)
- Represents files/data flowing between tasks
- State: PENDING → READY
- Fields: name, size, state, producer, consumers
- Tracks who produced and who consumes each data item

**Resource** (`resources.py`)
- Represents compute nodes
- Fields: id, name, speed (Gflop/s), cores, cores_available, memory, memory_available
- Mutable: cores_available and memory_available decrease as tasks are allocated

**Common** (`common.py`)
- Type alias: `Id = Union[str, int]`

---

## Layer 3: Simulator (`simulator.py`)

**Responsibility:** Orchestrate workflow execution

**Key Class:** `Simulator`

**Initialization (`__init__`):**
1. normalizeStartTasks() — Identify tasks with no parents
2. normalizeExitTasks() — Identify tasks with no children
3. calcAverageTransferRate() — Compute network speed
4. populateResources() — Build Resource objects from WFCommons machines
5. populateTasks() — Build Task objects, estimate exec times for each resource

**State Maintained:**
- tasks: dict[task_id → Task]
- resources: dict[resource_id → Resource]
- completed_tasks: list
- time: current simulation time
- start_task, exit_task: reference tasks

**Key Methods (Partially Implemented):**
- `start(scheduler)` — **INCOMPLETE** (entry point for execution; should call scheduler, then run event loop)
- `populateResources()` — ✓
- `populateTasks()` — ✓
- `estimateExecTime()` — ✓
- `calcAverageTransferRate()` — ⚠️ Incomplete (returns None; see calcDownwardRank)
- `calcDownwardRank()` — 🔴 BROKEN (no return statement; returns None)

---

## Layer 4: Scheduler (`schedulers/simple.py`)

**Responsibility:** Allocate tasks to resources

**Interface:** `Scheduler` base class (imported from `scheduler.py` — not found in codebase; may be external or missing)

**SimpleScheduler Implementation:**
- Strategy: Greedy (first-fit allocation)
- For each ready task:
  - Find first resource with sufficient cores and memory
  - Allocate task to that resource
  - Update resource availability
  - Return ScheduleTask action

**Limitations:**
- No task prioritization (FIFO)
- No topology awareness (ignores task dependencies for priority)
- No load balancing (picks first available)

---

## Data Flow: Task Execution (CONCEPTUAL — NOT IMPLEMENTED)

```
1. Scheduler allocates task T to resource R
   ↓
2. Simulator transitions T from READY → SCHEDULED
   ↓
3. Simulator waits for T's input dependencies to complete
   ↓
4. When all inputs ready: T → RUNNABLE
   ↓
5. Simulator calculates expected completion time: exec_time = T.flops / R.speed
   ↓
6. Simulator schedules T.end event at (current_time + exec_time)
   ↓
7. When event fires: T → DONE, outputs → READY
   ↓
8. Check if downstream tasks can transition to RUNNABLE
   ↓
9. Repeat until exit task completes
```

---

## Design Patterns in Use

**State Machine (Task states)**
- Clear transition rules
- Enum-based for type safety
- Currently only partially enforced

**Factory Pattern (Parser)**
- from_wfcommons() creates Workflow from external format

**Dependency Injection**
- Simulator takes workflow and scheduler as inputs
- Easy to swap schedulers

**Immutable Configuration**
- Config dataclass for parser settings

---

## Design Gaps & Issues

| Issue | Severity | Location | Impact |
|---|---|---|---|
| Execution loop missing | 🔴 CRITICAL | simulator.start() | Cannot run workflows |
| calcDownwardRank no return | 🔴 CRITICAL | simulator.py | Breaks initialization |
| Task exec state not tracked | 🔴 HIGH | task.py | Cannot measure metrics |
| No error handling | 🔴 HIGH | All layers | Crashes on invalid input |
| No event queue | 🔴 CRITICAL | simulator.py | No way to sequence events |
| Resource exhaustion not handled | ⚠️ MEDIUM | scheduler | May silently drop tasks |
| SimpleScheduler too simple | ⚠️ MEDIUM | schedulers/simple.py | Poor scheduling quality |

---

## Extension Points (For Future Versions)

1. **Schedulers:** Add new scheduler classes inheriting from Scheduler base
2. **Execution Models:** Swap event loop implementation (discrete event, time-stepped)
3. **Resource Types:** Extend Resource class for GPU, TPU, heterogeneous specs
4. **Data Transfer:** Implement network simulation layer (data_transfer.py)
5. **Task Failure:** Add retry logic to event loop
