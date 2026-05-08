# Code Conventions & Style

## Naming Conventions

**Classes:** PascalCase (Task, Workflow, Resource, SimpleScheduler)
- Dataclass convention: @dataclass decorator standard

**Functions:** snake_case (from_wfcommons, populate_resources, calc_average_transfer_rate)
- Method names: consistent snake_case

**Variables:** snake_case (task_id, resource_id, ready_tasks, completed_task_count)
- Acronyms preserved (e.g., wf_workflow, cpu_cores, io_transfer)

**Constants:** UPPER_SNAKE_CASE (not observed yet; recommend for hardcoded values)

**Module Names:** snake_case (wfcommons.py, simple.py)

---

## Type Hints

**Status:** Partial adoption (good in some files, missing in others)

**Present:**
- workflow.py: List[Task], Set[int], field(default_factory=list) — good
- parser/wfcommons.py: Dict[str, int], Set, pathlib.Path — good
- task.py: List[int], field — good

**Missing:**
- simulator.py: Many function returns untyped (calcAverageTransferRate, estimateExecTime)
- schedulers/simple.py: Limited type hints

**Recommendation:** Add type hints to all public methods:
```python
def start(self, scheduler: Scheduler) -> dict[str, Any]:
    ...

def estimate_exec_time(self, ref_resource: Resource, target: Resource, runtime: float) -> float:
    ...
```

---

## Indentation & Style

**Status:** 🔴 Inconsistent

**Observed:**
- parser/wfcommons.py: 4 spaces (PEP 8 compliant)
- schedulers/simple.py: 2-4 spaces (mixed)
- simulator.py: 2 spaces (non-standard)

**Recommendation:** 
- Apply Black formatter to entire codebase
- Target: 4 spaces, line length 100 (Black default)
- Command: `black research/`

---

## Docstring Style

**Status:** 🔴 Mostly missing

**Observed:**
- Few methods have any docstrings
- No module-level docstrings

**Recommendation:** Use Google-style docstrings:
```python
def from_wfcommons(file_path: str, config: Config) -> Workflow:
    """Parse WFCommons JSON file into a Workflow object.

    Args:
        file_path: Name of the JSON file in dag-instances/wfcommons/
        config: Parser configuration (ignore_memory, reference_speed)

    Returns:
        A fully constructed Workflow with tasks, data items, and resources.

    Raises:
        FileNotFoundError: If file_path does not exist.
        ValueError: If JSON is not valid WFCommons format.
    """
    ...
```

---

## Error Handling & Validation

**Status:** 🔴 None (code assumes inputs are valid)

**Recommend:**

1. **Parser validation:**
   ```python
   if not file_path.exists():
       raise FileNotFoundError(f"DAG file not found: {file_path}")
   if config.reference_speed <= 0:
       raise ValueError("reference_speed must be positive")
   ```

2. **Simulator validation:**
   ```python
   if not workflow.tasks:
       raise ValueError("Workflow has no tasks")
   ```

3. **Scheduler validation:**
   ```python
   if task_id not in workflow.tasks:
       raise ValueError(f"Task {task_id} not in workflow")
   ```

---

## Data Structure Conventions

**Dataclasses:** Standard pattern used (good)
```python
@dataclass
class Task:
    name: str
    flops: float
    memory: int
    state: TaskState = TaskState.READY
```

**Enums:** Used for Task states (TaskState enum with auto())

**Collections:**
- task_ids tracked as int (0-indexed)
- Workflow uses List for ordered access, Set for membership
- Recommendation: Consider using dict[task_id, Task] instead of separate list for clarity

**Immutability:**
- Config dataclass is effectively immutable (good)
- Workflow, Task, Resource are mutable (expected for simulation state)

---

## Import Organization

**Observed Pattern:**
```python
import os
import pathlib
from typing import Dict, Set
from wfcommons import wfinstances

from workflow import Workflow
from task import Task
```

**Recommendation:** Standardize with isort:
1. Standard library (os, pathlib, math, enum)
2. Third-party (wfcommons, numpy)
3. Local imports (workflow, task)
4. Blank line between groups

---

## Module Structure

**Current:**
- research/
  - *.py (models + entry point)
  - parser/ (parsing)
  - schedulers/ (scheduling strategies)

**Recommendation:** Consider adding:
- tests/ (unit tests, integration tests)
- metrics/ (metrics calculation, reporting)
- config/ (configuration files, constants)

---

## Logging

**Current:** Basic logging in main.py
```python
logging.basicConfig(level=logging.DEBUG, handlers=[logging.StreamHandler(sys.stdout)])
```

**Recommendation:** Extend to simulator and scheduler:
```python
logger = logging.getLogger(__name__)
logger.info(f"Task {task_id} allocated to {resource_id}")
logger.warning(f"Resource {resource_id} out of memory")
```

---

## Testing Conventions (Not Implemented Yet)

**Recommend pytest structure:**
```
tests/
├── conftest.py (fixtures: sample workflows, resources)
├── test_parser.py (parser tests)
├── test_simulator.py (simulator tests)
├── test_schedulers.py (scheduler tests)
└── integration/ (end-to-end tests with real DAGs)
```

**Test naming:** `test_<function>_<condition>_<expected_result>`
Example: `test_simulator_start_completes_workflow_with_valid_dag`

---

## Git Commit Message Convention

**Recommend conventional commits:**
```
feat(simulator): implement event loop with task scheduling
fix(parser): handle missing machine speed in WFCommons JSON
test(schedulers): add unit tests for SimpleScheduler
docs(architecture): document execution flow
```

Format: `<type>(<scope>): <message>`

Types: feat, fix, test, docs, refactor, style, perf, chore

---

## Summary Table

| Aspect | Status | Priority | Action |
|---|---|---|---|
| Naming conventions | ✓ Good | - | No action needed |
| Type hints | ⚠️ Partial | HIGH | Add return types to simulator, scheduler |
| Indentation | 🔴 Inconsistent | HIGH | Run Black formatter |
| Docstrings | 🔴 Missing | HIGH | Add Google-style docstrings |
| Error handling | 🔴 None | CRITICAL | Add validation in all layers |
| Logging | ⚠️ Minimal | MEDIUM | Extend to simulator, scheduler |
| Testing | 🔴 None | HIGH | Create pytest suite |
| Module structure | ✓ Good | - | No action needed |
