# Testing Strategy & Coverage

**Current Status:** 🔴 No tests exist

**Recommendation:** Adopt pytest as test framework

## Testing Pyramid

```
                  ╱╲
                 ╱  ╲        E2E Tests (3-5)
                ╱    ╲       Real DAGs, full runs
               ╱──────╲
              ╱        ╲     Integration Tests (10-15)
             ╱          ╲    Parser + Simulator, Scheduler + Simulator
            ╱────────────╲
           ╱              ╲  Unit Tests (30-50)
          ╱                ╲ Models, functions, methods
         ╱__________________╲
```

---

## Unit Tests (30-50 tests)

**Domain Models (task.py, data_item.py, workflow.py, resources.py)**

| Test | Purpose | Example |
|---|---|---|
| test_task_creation | Task instantiates with correct state | `task.state == TaskState.READY` |
| test_task_state_transitions | State changes are valid | `READY → RUNNABLE` allowed, `DONE → RUNNING` rejected |
| test_workflow_add_task | Tasks added to workflow with correct ID | `workflow.add_task(task) → 0, 1, 2...` |
| test_workflow_add_data_dependency | Dependencies tracked correctly | `consumer.inputs` contains data_item_id |
| test_resource_allocation | Resource cores/memory decrement | `resource.cores_available` decreases when task allocated |
| test_data_item_state | Data item transitions PENDING → READY | Consumer count affects consumer state |

**Parser (parser/wfcommons.py)**

| Test | Purpose | Example |
|---|---|---|
| test_from_wfcommons_loads_json | JSON file parsed successfully | `workflow.tasks` populated |
| test_config_defaults | Config uses sensible defaults | `reference_speed=10.0` if not specified |
| test_size_conversion | Byte → MB conversion accurate | `convert_bytes_to_mb(1_000_000) == 1` |
| test_task_dependency_preserved | Task DAG structure intact | `workflow.tasks[1].parents contains workflow.tasks[0].id` |
| test_resource_estimation | Exec times estimated for heterogeneous resources | `resource_A_time != resource_B_time` if speeds differ |
| test_invalid_json_raises | Bad JSON file raises error | `FileNotFoundError`, `ValueError` |

**Simulator (simulator.py)**

| Test | Purpose | Example |
|---|---|---|
| test_simulator_init | Initialization completes without errors | `simulator.start_task`, `simulator.exit_task` set |
| test_normalizeStartTasks | Start tasks correctly identified | Tasks with no parents marked as start |
| test_normalizeExitTasks | Exit tasks correctly identified | Tasks with no children marked as exit |
| test_populateResources | Resources created from WFCommons | `len(simulator.resources) > 0` |
| test_populateTasks | Tasks mapped to resources | `simulator.tasks` populated with exec times per resource |
| test_estimateExecTime | Heterogeneous execution times calculated | Slower resources → longer times |

**Scheduler (schedulers/simple.py)**

| Test | Purpose | Example |
|---|---|---|
| test_simple_scheduler_allocates_ready_tasks | Ready tasks allocated to resources | Return list of ScheduleTask |
| test_simple_scheduler_respects_resource_limits | Does not over-allocate cores/memory | `resource.cores_available >= 0` after allocation |
| test_simple_scheduler_empty_workflow | Handles workflow with no tasks | Returns empty list |
| test_simple_scheduler_task_not_found | Invalid task ID raises error | ValueError if task_id not in workflow |

---

## Integration Tests (10-15 tests)

**Parser → Simulator**

| Test | Purpose |
|---|---|
| test_full_parse_and_init | Parse real DAG, initialize simulator successfully |
| test_parse_bwa_workflow | bwa-chameleon-small-001.json → valid Workflow object |
| test_parse_blast_workflow | blast-chameleon-large-002.json → valid Workflow object |
| test_parse_1000genome_workflow | 1000genome-chameleon-16ch-250k-001.json → valid Workflow object |

**Scheduler → Simulator**

| Test | Purpose |
|---|---|
| test_scheduler_allocation_and_resource_update | SimpleScheduler allocates, resources updated correctly |
| test_scheduler_handles_no_available_resources | Gracefully handles resource exhaustion |

**End-to-End (Partial Execution)**

| Test | Purpose |
|---|---|
| test_simulator_initialization_completes | Simulator init doesn't crash on real DAG |
| test_scheduler_and_simulator_compatible | Scheduler output matches Simulator input expectations |
| test_metrics_collection | Metrics (makespan, task times) collected during simulation |

---

## End-to-End Tests (3-5 tests)

**Full Workflow Execution**

| Test | Purpose | Criteria |
|---|---|---|
| test_bwa_workflow_completes | bwa DAG runs to exit task | `workflow.completed_task_count == len(workflow.tasks)` |
| test_blast_workflow_completes | blast DAG runs to exit task | Same criterion |
| test_1000genome_workflow_completes | 1000genome DAG runs to exit task | Same criterion |
| test_metrics_recorded | Makespan and task times recorded | Metrics dict has entries for all tasks |
| test_execution_time_reasonable | Execution completes in reasonable wall time | < 10 seconds for small DAGs |

---

## Testing Infrastructure

**Framework:** pytest

**Installation:**
```bash
pip install pytest pytest-cov pytest-timeout
```

**Fixtures (conftest.py):**

```python
@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(name="sample", flops=100.0, memory=512, min_cores=1, max_cores=4)

@pytest.fixture
def sample_workflow():
    """Create a simple workflow with 3 tasks."""
    w = Workflow()
    t1 = Task(name="t1", flops=100.0, memory=512, min_cores=1, max_cores=4)
    t2 = Task(name="t2", flops=200.0, memory=1024, min_cores=2, max_cores=8)
    t3 = Task(name="t3", flops=150.0, memory=256, min_cores=1, max_cores=2)
    w.add_task(t1)
    w.add_task(t2)
    w.add_task(t3)
    # Add dependencies: t1 → t2 → t3
    ...
    return w

@pytest.fixture
def sample_resources():
    """Create a set of sample resources."""
    return {
        "cpu1": Resource(id="cpu1", name="CPU1", speed=10.0, cores=8, ...),
        "cpu2": Resource(id="cpu2", name="CPU2", speed=5.0, cores=4, ...),
    }

@pytest.fixture
def real_bwa_workflow():
    """Load real bwa DAG from file."""
    return from_wfcommons("bwa-chameleon-small-001.json", Config())
```

**Directory Structure:**
```
research/
├── tests/
│   ├── conftest.py                    # Fixtures and helpers
│   ├── test_task.py                   # Task model tests
│   ├── test_workflow.py                # Workflow model tests
│   ├── test_parser.py                  # Parser tests
│   ├── test_simulator.py               # Simulator tests
│   ├── test_schedulers.py              # Scheduler tests
│   └── integration/
│       ├── test_parser_simulator.py    # Parser → Simulator integration
│       ├── test_scheduler_simulator.py # Scheduler → Simulator integration
│       └── test_end_to_end.py          # Full workflow execution
```

---

## Test Execution

**Run all tests:**
```bash
pytest tests/ -v
```

**Run with coverage:**
```bash
pytest tests/ --cov=. --cov-report=html
```

**Run only unit tests:**
```bash
pytest tests/ -m "not integration" -v
```

**Run only integration tests:**
```bash
pytest tests/integration/ -v
```

**Run specific test:**
```bash
pytest tests/test_simulator.py::test_simulator_init -v
```

**Run with timeout (for e2e):**
```bash
pytest tests/integration/test_end_to_end.py --timeout=30 -v
```

---

## Gate Checks (Pre-Commit)

Before committing, ensure:

1. **All unit tests pass:**
   ```bash
   pytest tests/ -v
   ```

2. **Coverage ≥ 70%:**
   ```bash
   pytest tests/ --cov=. --cov-report=term-missing | grep -E "TOTAL|test"
   ```

3. **No lint issues:**
   ```bash
   black research/ --check
   flake8 research/ --max-line-length=100
   ```

4. **Type hints valid:**
   ```bash
   mypy research/ --ignore-missing-imports
   ```

---

## Coverage Goals

| Component | Target | Strategy |
|---|---|---|
| Domain models (task, workflow, etc.) | 100% | Test all methods and edge cases |
| Parser | 90%+ | Test valid/invalid JSON, edge cases |
| Simulator | 85%+ | Test init, population, but execution loop tested via e2e |
| Scheduler | 90%+ | Test allocation logic, edge cases |
| **Overall** | **80%+** | Good balance of unit + integration |

---

## Test Naming Convention

**Pattern:** `test_<component>_<condition>_<expected_result>`

**Examples:**
- `test_task_state_transitions_valid_allowed`
- `test_workflow_add_task_increments_task_id`
- `test_parser_invalid_json_raises_value_error`
- `test_simulator_init_with_real_dag_completes`
- `test_scheduler_no_resources_returns_empty_list`

---

## Known Challenges & Workarounds

| Challenge | Workaround |
|---|---|
| Execution loop incomplete | Test scheduler in isolation; use mock simulator for now |
| No real metrics collection yet | Add placeholder metrics to Simulator; expand in v1.1 |
| Large DAG files slow tests | Use small subset DAG or synthetic workflow for unit tests |
| Resource timing non-deterministic | Use fixed random seed; avoid wall-clock time assertions |

---

## Phased Test Implementation

**Phase 1 (v1.0 blocking):**
- Unit tests for domain models (task, workflow, resource)
- Unit tests for parser
- Unit tests for scheduler
- Estimate: 20-30 tests, 2-3 hours

**Phase 2 (v1.0 completion):**
- Integration tests (parser + simulator)
- End-to-end tests with real DAGs
- Estimate: 10-15 tests, 3-4 hours

**Phase 3 (v1.1):**
- Performance tests (execution time)
- Comparison tests between schedulers
- Estimate: 5-10 tests, 2-3 hours
